"""Prompt v1.2.0 and parser behavior used for the v2 labeling report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, ValidationError

PROMPT_VERSION = "1.2.0"
PROMPT_MODEL = "gemini-2.5-pro"
PROMPT_PROVIDER = "vertex_ai"

SYSTEM_PROMPT = """
Bạn là biên tập viên báo chí tiếng Việt. Tóm tắt phải:
- Trung thực 100% với bài gốc; KHÔNG suy diễn, KHÔNG bịa số liệu hay tên riêng.
- 2-3 câu, tổng cộng 40-70 từ.
- Văn phong báo chí, trung lập, không cảm thán, không câu hỏi.
- Giữ nguyên tên riêng, số liệu, ngày tháng đúng như bài gốc.
- Nếu thông tin không đủ rõ, viết câu trung lập, KHÔNG bổ sung từ kiến thức ngoài.
""".strip()

USER_TEMPLATE = """
Tiêu đề: {title}
Chuyên mục: {category}
Nguồn: {source}

Nội dung:
\"\"\"
{content_text}
\"\"\"

Trả về JSON đúng schema:
{{
  "summary": "...",
  "key_entities": ["..."],
  "confidence": 0.0,
  "refusal_reason": null
}}
""".strip()


@dataclass(slots=True)
class GenerationParams:
    temperature: float = 0.2
    top_p: float = 0.9
    max_output_tokens: int = 4096
    response_mime_type: str = "application/json"


@dataclass(slots=True)
class QcConfig:
    min_words: int = 40
    max_words: int = 90
    min_sentences: int = 2
    max_sentences: int = 4
    entity_fuzzy_min_ratio: float = 0.85


class LabelOutput(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    refusal_reason: str | None = None


def render_user_prompt(
    *,
    title: str,
    category: str | None,
    source: str,
    content_text: str,
    content_max_chars: int = 6000,
) -> str:
    snippet = content_text or ""
    if len(snippet) > content_max_chars:
        snippet = snippet[:content_max_chars].rsplit(" ", 1)[0] + " [...]"
    return USER_TEMPLATE.format(
        title=title or "",
        category=category or "",
        source=source,
        content_text=snippet,
    )


def parse_label_json(raw_text: str) -> LabelOutput:
    """Parse Gemini JSON output with the hardening from commit 8e8dda8."""
    try:
        data: Any = json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            data = json.loads(raw_text, strict=False)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {exc}") from exc
    if isinstance(data, dict):
        confidence = data.get("confidence")
        if isinstance(confidence, int | float) and confidence > 1.0:
            data["confidence"] = 1.0
        if data.get("summary") is None and data.get("refusal_reason"):
            data["summary"] = ""
    try:
        return LabelOutput(**data)
    except ValidationError as exc:
        raise ValueError(f"LLM JSON does not match schema: {exc}") from exc
