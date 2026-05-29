"""Google AI Studio (Gemini) client with multi-key rotation for labeling.

Labeling runs on free AI Studio API keys.  Multiple keys can be supplied
(comma-separated in the env-var or passed as a list) so that when one key
hits a rate / quota limit the next key is tried automatically.

Default model: gemini-3.1-flash-lite (configurable via model_chain).
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
    "gemini-3.1-flash-lite",
]


class GeminiLLMError(RuntimeError):
    """Unrecoverable error from AI Studio."""


class GeminiTransientError(RuntimeError):
    """Retryable error (rate-limit, timeout, transient server error)."""


OverrideFn = Callable[[str, str], str]


class GeminiLabeler:
    """AI Studio labeler with key rotation and model fallback.

    Each call to :meth:`generate` iterates over a **local copy** of the key
    list so that concurrent threads (via ``asyncio.to_thread``) never share
    mutable rotation state.  This avoids race conditions where one thread's
    quota error cascades into marking other threads' keys as exhausted.
    """

    def __init__(
        self,
        *,
        api_keys: list[str] | None = None,
        model_chain: list[str] | None = None,
        params: GenerationParams | None = None,
        override_callable: OverrideFn | None = None,
    ) -> None:
        raw_keys = api_keys or _keys_from_env()
        if not raw_keys:
            raise GeminiLLMError("No API keys provided for AI Studio labeling")
        self._keys: list[str] = list(raw_keys)
        self._model_chain = model_chain or list(DEFAULT_MODEL_CHAIN)
        self.params = params or GenerationParams()
        self._override = override_callable
        self._clients: dict[str, Any] = {}
        self._clients_lock = threading.Lock()

    def _get_client(self, api_key: str) -> Any:
        with self._clients_lock:
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
        """Generate a label using AI Studio.

        Key rotation and model fallback are handled per-call using local
        iteration over snapshot copies of keys and models.  This is safe
        for concurrent use from multiple threads.
        """
        if self._override is not None:
            return self._override(system, user)

        from google.genai import types

        keys = list(self._keys)
        models = list(self._model_chain)
        last_exc: Exception | None = None

        for model_name in models:
            for key_idx, api_key in enumerate(keys):
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
                except GeminiLLMError:
                    raise
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
                            "Key #%d/%d quota hit on %s: %s",
                            key_idx + 1,
                            len(keys),
                            model_name,
                            exc,
                        )
                        last_exc = exc
                        continue
                    if is_transient:
                        raise GeminiTransientError(str(exc)) from exc
                    if "not found" in err or "does not exist" in err or "invalid" in err:
                        log.warning("Model %s not available, trying next: %s", model_name, exc)
                        last_exc = exc
                        break
                    raise GeminiLLMError(str(exc)) from exc
            else:
                last_exc = last_exc or RuntimeError(f"All keys exhausted for {model_name}")
                continue
            continue

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
