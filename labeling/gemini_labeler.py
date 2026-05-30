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
    """AI Studio labeler with round-robin key rotation and model fallback.

    Every call to :meth:`generate` starts on a different key (advanced by a
    shared round-robin cursor) and then tries the remaining keys in order on
    rate-limit / transient errors.  This spreads load across **all** provided
    keys instead of hammering ``keys[0]`` until it is exhausted, and it keeps
    rotation safe for concurrent threads (via ``asyncio.to_thread``).
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
        # Round-robin cursor so concurrent calls start on different keys
        # instead of all hammering keys[0] first.
        self._rr_lock = threading.Lock()
        self._rr_counter = 0

    def _key_order(self) -> list[tuple[int, str]]:
        """Return ``(original_index, key)`` pairs starting at a rotating offset.

        Each call advances a shared counter so that concurrent requests spread
        their first attempt across all keys, rather than every call starting at
        ``keys[0]``.  The full key list is still tried on errors, just in a
        rotated order.
        """
        n = len(self._keys)
        with self._rr_lock:
            start = self._rr_counter % n
            self._rr_counter = (self._rr_counter + 1) % n
        return [((start + i) % n, self._keys[(start + i) % n]) for i in range(n)]

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

        Keys are tried in round-robin order (see :meth:`_key_order`) with
        model fallback.  When every key hits a rate-limit/transient error the
        method raises :class:`GeminiTransientError` so the ``@retry`` decorator
        backs off and retries instead of failing permanently.
        """
        if self._override is not None:
            return self._override(system, user)

        from google.genai import types

        models = list(self._model_chain)
        n_keys = len(self._keys)
        last_exc: Exception | None = None
        saw_rate_limit = False

        for model_name in models:
            model_unavailable = False
            for key_idx, api_key in self._key_order():
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
                    if is_quota or is_transient:
                        kind = "quota" if is_quota else "transient error"
                        log.warning(
                            "Key #%d/%d %s on %s, trying next key: %s",
                            key_idx + 1,
                            n_keys,
                            kind,
                            model_name,
                            exc,
                        )
                        last_exc = exc
                        saw_rate_limit = True
                        continue
                    if "not found" in err or "does not exist" in err or "invalid" in err:
                        log.warning("Model %s not available, trying next: %s", model_name, exc)
                        last_exc = exc
                        model_unavailable = True
                        break
                    raise GeminiLLMError(str(exc)) from exc
            if model_unavailable:
                continue

        if saw_rate_limit:
            raise GeminiTransientError(
                f"All {n_keys} key(s) hit rate-limit/transient errors. Last error: {last_exc}"
            )
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
