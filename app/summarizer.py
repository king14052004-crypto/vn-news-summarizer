"""ViT5/LoRA summarizer loaded from Hugging Face Hub or a local path."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class GenerationConfig:
    max_input_length: int = 1024
    max_new_tokens: int = 128
    num_beams: int = 4
    no_repeat_ngram_size: int = 3
    length_penalty: float = 1.0
    early_stopping: bool = True
    batch_size: int = 4


class ViT5Summarizer:
    """Lazy wrapper around the fine-tuned ViT5 model.

    The expected production/demo value is ``HF_MODEL_ID`` pointing to the
    model or LoRA adapter equivalent to ``models/vit5-news-v2/checkpoint-309``.
    If the ID is a PEFT adapter, ``HF_BASE_MODEL_ID`` may override the
    base model; otherwise the adapter config's base model is used.
    """

    def __init__(
        self,
        model_id: str | None = None,
        *,
        base_model_id: str | None = None,
        token: str | None = None,
        device: str | None = None,
        generation: GenerationConfig | None = None,
    ) -> None:
        self.model_id = model_id or os.environ.get("HF_MODEL_ID") or "VietAI/vit5-base"
        self.base_model_id = base_model_id or os.environ.get("HF_BASE_MODEL_ID")
        self.token = token if token is not None else os.environ.get("HF_TOKEN")
        self.device = device or os.environ.get("MODEL_DEVICE")
        self.generation = generation or GenerationConfig()
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    def _load_as_peft_adapter(self, transformers: Any) -> tuple[Any, Any] | None:
        try:
            from peft import PeftConfig, PeftModel

            peft_cfg = PeftConfig.from_pretrained(self.model_id, token=self.token)
            base_name = self.base_model_id or peft_cfg.base_model_name_or_path
            base_model = transformers.AutoModelForSeq2SeqLM.from_pretrained(
                base_name,
                token=self.token,
            )
            model = PeftModel.from_pretrained(base_model, self.model_id, token=self.token)
            tokenizer_source = self.model_id
            if Path(self.model_id).exists() and not (Path(self.model_id) / "tokenizer.json").exists():
                tokenizer_source = base_name
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                tokenizer_source,
                token=self.token,
            )
            return model, tokenizer
        except Exception:
            return None

    def _ensure_loaded(self) -> tuple[Any, Any]:
        if self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer

        import transformers

        loaded = self._load_as_peft_adapter(transformers)
        if loaded is None:
            model = transformers.AutoModelForSeq2SeqLM.from_pretrained(
                self.model_id,
                token=self.token,
            )
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.model_id,
                token=self.token,
            )
        else:
            model, tokenizer = loaded

        if self.device:
            model.to(self.device)
        model.eval()
        self._model = model
        self._tokenizer = tokenizer
        return model, tokenizer

    def summarize(self, text: str) -> str:
        return self.summarize_batch([text])[0] if text and text.strip() else ""

    def summarize_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        empty_mask = [not text or not text.strip() for text in texts]
        non_empty = [text for text, is_empty in zip(texts, empty_mask, strict=True) if not is_empty]
        if not non_empty:
            return ["" for _ in texts]

        model, tokenizer = self._ensure_loaded()
        decoded: list[str] = []
        for start in range(0, len(non_empty), self.generation.batch_size):
            batch = non_empty[start : start + self.generation.batch_size]
            inputs = tokenizer(
                batch,
                max_length=self.generation.max_input_length,
                truncation=True,
                padding=True,
                return_tensors="pt",
            )
            if self.device:
                inputs = {key: value.to(self.device) for key, value in inputs.items()}
            outputs = model.generate(
                **inputs,
                max_new_tokens=self.generation.max_new_tokens,
                num_beams=self.generation.num_beams,
                no_repeat_ngram_size=self.generation.no_repeat_ngram_size,
                length_penalty=self.generation.length_penalty,
                early_stopping=self.generation.early_stopping,
            )
            decoded.extend(str(x) for x in tokenizer.batch_decode(outputs, skip_special_tokens=True))

        result: list[str] = []
        cursor = 0
        for is_empty in empty_mask:
            if is_empty:
                result.append("")
            else:
                result.append(decoded[cursor])
                cursor += 1
        return result
