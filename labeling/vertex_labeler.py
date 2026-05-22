"""Thin Vertex AI Gemini client for generating teacher summaries."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from labeling.prompt import GenerationParams


class VertexLLMError(RuntimeError):
    """Raised when Vertex returns an unrecoverable error."""


class VertexTransientError(RuntimeError):
    """Raised for retryable Vertex/network failures."""


OverrideFn = Callable[[str, str], str]


class VertexLabeler:
    def __init__(
        self,
        *,
        project: str | None = None,
        location: str | None = None,
        model_name: str = "gemini-2.5-pro",
        params: GenerationParams | None = None,
        override_callable: OverrideFn | None = None,
    ) -> None:
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
        self.model_name = model_name
        self.params = params or GenerationParams()
        self._override = override_callable
        self._model: Any | None = None

    def _ensure_model(self) -> Any:
        if self._override is not None:
            return None
        if self._model is not None:
            return self._model
        if not self.project:
            raise VertexLLMError("GOOGLE_CLOUD_PROJECT is not set")

        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=self.project, location=self.location)
        self._model = GenerativeModel(self.model_name)
        return self._model

    @retry(
        reraise=True,
        retry=retry_if_exception_type(VertexTransientError),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
    )
    def generate(self, *, system: str, user: str) -> str:
        if self._override is not None:
            return self._override(system, user)

        from vertexai.generative_models import Content, GenerationConfig, Part

        model = self._ensure_model()
        generation_config = GenerationConfig(
            temperature=self.params.temperature,
            top_p=self.params.top_p,
            max_output_tokens=self.params.max_output_tokens,
            response_mime_type=self.params.response_mime_type,
        )
        try:
            response = model.generate_content(
                [Content(role="user", parts=[Part.from_text(f"{system}\n\n{user}")])],
                generation_config=generation_config,
            )
        except Exception as exc:
            text = str(exc).lower()
            if any(
                marker in text
                for marker in (
                    "429",
                    "deadline",
                    "unavailable",
                    "internal",
                    "timeout",
                    "resource has been exhausted",
                )
            ):
                raise VertexTransientError(str(exc)) from exc
            raise VertexLLMError(str(exc)) from exc
        try:
            return str(response.text)
        except Exception as exc:
            raise VertexLLMError(f"empty/blocked response: {exc}") from exc
