"""Deterministic QC checks used before exporting training data."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - fallback for minimal validation environments.
    from difflib import SequenceMatcher

    class _FuzzFallback:
        @staticmethod
        def partial_ratio(a: str, b: str) -> float:
            return SequenceMatcher(None, a, b).ratio() * 100

    fuzz = _FuzzFallback()

from labeling.prompt import LabelOutput, QcConfig

_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")
_NUMERIC = re.compile(r"\S*\d[\S]*")
_PUNCT_RE = re.compile(r"[\s\-\u2013\u2014\.\,;:\(\)\[\]\{\}/]+")
_DIGIT_GROUP = re.compile(r"\d{3,}")
_TITLE_CHARS = (
    "A-ZĐÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆ"
    "ÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ"
)
_ENTITY = re.compile(rf"(?:[{_TITLE_CHARS}][\wÀ-ỹ]*(?:\s+[{_TITLE_CHARS}][\wÀ-ỹ]*)+)")


@dataclass(slots=True)
class QcResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0
    missing_numbers: list[str] = field(default_factory=list)
    missing_entities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "reasons": self.reasons,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "missing_numbers": self.missing_numbers,
            "missing_entities": self.missing_entities,
        }


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").strip()


def _word_count(text: str) -> int:
    return len(_norm(text).split())


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENT_SPLIT.split(_norm(text)) if part.strip()]


def _numerics(text: str) -> list[str]:
    out: list[str] = []
    for match in _NUMERIC.finditer(text):
        token = match.group(0).strip(".,;:%()[]{}")
        if token:
            out.append(token)
    return out


def _collapse_punct(text: str) -> str:
    return _PUNCT_RE.sub(" ", text).strip()


def _contains_numeric(source: str, token: str) -> bool:
    if token in source:
        return True
    collapsed_source = _collapse_punct(source)
    collapsed_token = _collapse_punct(token)
    if collapsed_token and collapsed_token in collapsed_source:
        return True
    groups = _DIGIT_GROUP.findall(token)
    return bool(groups and all(group in source for group in groups))


def _entities(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for match in _ENTITY.finditer(text):
        entity = match.group(0).strip()
        if entity and entity not in seen:
            seen.add(entity)
            out.append(entity)
    return out


def _contains_entity(source: str, entity: str, *, min_ratio: float) -> bool:
    if entity in source:
        return True
    collapsed_source = _collapse_punct(source)
    collapsed_entity = _collapse_punct(entity)
    if collapsed_entity and collapsed_entity in collapsed_source:
        return True
    if fuzz.partial_ratio(entity, source) >= min_ratio * 100:
        return True
    return any(len(token) >= 4 and token in source for token in entity.split())


def run_qc(*, output: LabelOutput, source_text: str, cfg: QcConfig | None = None) -> QcResult:
    cfg = cfg or QcConfig()
    summary = _norm(output.summary)
    source = _norm(source_text)
    reasons: list[str] = []

    if output.refusal_reason:
        reasons.append(f"llm_refusal:{output.refusal_reason}")

    wc = _word_count(summary)
    if wc < cfg.min_words:
        reasons.append(f"too_short:{wc}<{cfg.min_words}")
    if wc > cfg.max_words:
        reasons.append(f"too_long:{wc}>{cfg.max_words}")

    sentence_count = len(_sentences(summary))
    if sentence_count < cfg.min_sentences:
        reasons.append(f"too_few_sentences:{sentence_count}<{cfg.min_sentences}")
    if sentence_count > cfg.max_sentences:
        reasons.append(f"too_many_sentences:{sentence_count}>{cfg.max_sentences}")

    missing_numbers = [token for token in _numerics(summary) if not _contains_numeric(source, token)]
    if missing_numbers:
        reasons.append(f"unsupported_numbers:{','.join(missing_numbers[:5])}")

    missing_entities = [
        entity
        for entity in _entities(summary)
        if not _contains_entity(source, entity, min_ratio=cfg.entity_fuzzy_min_ratio)
    ]
    if missing_entities:
        reasons.append(f"unsupported_entities:{','.join(missing_entities[:5])}")

    return QcResult(
        passed=not reasons,
        reasons=reasons,
        word_count=wc,
        sentence_count=sentence_count,
        missing_numbers=missing_numbers,
        missing_entities=missing_entities,
    )
