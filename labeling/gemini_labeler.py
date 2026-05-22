"""Google AI Studio (Gemini) client with multi-key rotation for labeling.

Replaces the Vertex AI backend so that labeling can run on free AI Studio
API keys instead of a paid GCP project.  Multiple keys can be supplied
(comma-separated in the env-var or passed as a list) so that when one key
hits a rate / quota limit the next key is tried automatically.

Model fallback order (configurable):
    gemini-2.5-flash  →  gemini-2.0-flash
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from labeling.prompt import GenerationParams

log = logging.getLogger(__name__)

DEFAULT_MODEL_CHAIN: list[str] = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


class GeminiLLMError(RuntimeError):
    """Unrecoverable error from AI Studio."""


class GeminiTransientError(RuntimeError):
    """Retryable error (rate-limit, timeout, transient server error)."""


OverrideFn = Callable[[str, str], str]


class _KeyRing:
    """Thread-safe round-robin key pool with exhaustion tracking."""

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            raise GeminiLLMError("No API keys provided for AI Studio labeling")
        self._keys = list(keys)
        self._idx = 0
        self._exhausted: set[int] = set()
        self._lock = threading.Lock()

    @property
    def total(self) -> int:
        return len(self._keys)

    def current(self) -> str:
        with self._lock:
            return self._keys[self._idx]

    def mark_exhausted(self) -> str | None:
        """Mark the current key as exhausted and rotate. Return the next
        usable key, or *None* if every key is exhausted."""
        with self._lock:
            self._exhausted.add(self._idx)
            for offset in range(1, len(self._keys) + 1):
                candidate = (self._idx + offset) % len(self._keys)
                if candidate not in self._exhausted:
                    self._idx = candidate
                    log.info("Rotated to API key #%d/%d", candidate + 1, len(self._keys))
                    return self._keys[candidate]
            return None

    def reset(self) -> None:
        with self._lock:
            self._exhausted.clear()
            self._idx = 0


class GeminiLabeler:
    """AI Studio labeler with key rotation and model fallback."""

    def __init__(
        self,
        *,
        api_keys: list[str] | None = None,
        model_chain: list[str] | None = None,
        params: GenerationParams | None = None,
        override_callable: OverrideFn | None = None,
    ) -> None:
        raw_keys = api_keys or _keys_from_env()
        self._keyring = _KeyRing(raw_keys)
        self._model_chain = model_chain or list(DEFAULT_MODEL_CHAIN)
        self.params = params or GenerationParams()
        self._override = override_callable
        self._clients: dict[str, Any] = {}

    def _get_client(self, api_key: str) -> Any:
        if api_key not in self._clients:
            from google import genai

            self._clients[api_key] = genai.Client(api_key=api_key)
        return self._clients[api_key]

    @retry(
        reraise=True,
        retry=retry_if_exception_type(GeminiTransientError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(6),
    )
    def generate(self, *, system: str, user: str) -> str:
        if self._override is not None:
            return self._override(system, user)

        from google.genai import types

        last_exc: Exception | None = None
        for model_name in self._model_chain:
            self._keyring.reset()
            while True:
                api_key = self._keyring.current()
                client = self._get_client(api_key)
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"{system}\n\n{user}",
                        config=types.GenerateContentConfig(
                            temperature=self.params.temperature,
                            top_p=self.params.top_p,
                            max_output_tokens=self.params.max_output_tokens,
                            response_mime_type=self.params.response_mime_type,
                        ),
                    )
                    text = response.text
                    if text is None:
                        raise GeminiLLMError(
                            f"empty/blocked response from {model_name}"
                        )
                    return str(text)
                except Exception as exc:
                    err = str(exc).lower()
                    is_quota = any(
                        m in err
                        for m in (
                            "429",
                            "resource has been exhausted",
                            "quota",
                            "rate limit",
                            "rate_limit",
                            "too many requests",
                        )
                    )
                    is_transient = any(
                        m in err
                        for m in (
                            "deadline",
                            "unavailable",
                            "internal",
                            "timeout",
                            "503",
                            "500",
                        )
                    )
                    if is_quota:
                        log.warning(
                            "Key #%d quota hit on %s: %s",
                            self._keyring._idx + 1,
                            model_name,
                            exc,
                        )
                        next_key = self._keyring.mark_exhausted()
                        if next_key is not None:
                            continue
                        last_exc = exc
                        break
                    if is_transient:
                        raise GeminiTransientError(str(exc)) from exc
                    if "not found" in err or "does not exist" in err or "invalid" in err:
                        log.warning("Model %s not available, trying next: %s", model_name, exc)
                        last_exc = exc
                        break
                    raise GeminiLLMError(str(exc)) from exc

        raise GeminiLLMError(
            f"All models/keys exhausted. Last error: {last_exc}"
        )


def _keys_from_env() -> list[str]:
    """Read comma-separated API keys from ``GEMINI_API_KEYS``."""
    raw = os.environ.get("GEMINI_API_KEYS", "").strip()
    if not raw:
        single = os.environ.get("GEMINI_API_KEY", "").strip()
        if single:
            return [single]
        raise GeminiLLMError(
            "Set GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY in your environment"
        )
    return [k.strip() for k in raw.split(",") if k.strip()]
