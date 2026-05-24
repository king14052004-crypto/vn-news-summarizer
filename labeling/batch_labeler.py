"""Batch labeling with gemini-3.1-flash-lite and multi-key rotation.

Designed for labeling large datasets (thousands of articles) using free-tier
AI Studio keys.  Features:

- Rate-limit-aware: respects 15 RPM per project via configurable delay.
- Key rotation: distributes requests round-robin across API keys (each key =
  separate project = separate 500 RPD quota).
- Resumable: writes results incrementally and skips already-processed articles.

Free-tier limits (gemini-3.1-flash-lite, May 2026):
    15 RPM  |  500 RPD/project  |  250K TPM

Example (9 keys):
    9 keys × 500 RPD = 4,500 req/day → 2810 articles in < 1 day
    15 RPM → delay 4s between requests → ~3.1 hours total
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from labeling.gemini_labeler import GeminiLabeler, GeminiLLMError, GeminiTransientError
from labeling.prompt import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    GenerationParams,
    parse_label_json,
    render_user_prompt,
)
from labeling.qc import run_qc

log = logging.getLogger(__name__)

MODEL = "gemini-3.1-flash-lite"
RPM = 15
RPD_PER_KEY = 500
SAFE_DELAY = 4.5  # seconds between requests (slightly > 60/15)
SAFE_RPD_BUDGET = 450  # conservative daily budget per key


@dataclass(slots=True)
class BatchConfig:
    """Configuration for batch labeling."""

    batch_size: int = 50
    delay_between_requests: float = SAFE_DELAY
    max_per_key_per_day: int = SAFE_RPD_BUDGET


@dataclass
class KeyUsageTracker:
    """Track per-key daily usage to avoid exceeding RPD."""

    daily_counts: dict[str, int] = field(default_factory=dict)
    budget_per_key: int = SAFE_RPD_BUDGET

    def can_use(self, key_index: int) -> bool:
        return self.daily_counts.get(str(key_index), 0) < self.budget_per_key

    def record_use(self, key_index: int) -> None:
        k = str(key_index)
        self.daily_counts[k] = self.daily_counts.get(k, 0) + 1

    def get_next_available(self, total_keys: int, start: int = 0) -> int | None:
        for offset in range(total_keys):
            idx = (start + offset) % total_keys
            if self.can_use(idx):
                return idx
        return None

    def total_remaining(self, total_keys: int) -> int:
        return sum(
            self.budget_per_key - self.daily_counts.get(str(i), 0)
            for i in range(total_keys)
        )


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_existing_ids(output_path: Path) -> set[int]:
    if not output_path.exists():
        return set()
    ids: set[int] = set()
    with output_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    row = json.loads(line)
                    if "article_id" in row:
                        ids.add(row["article_id"])
                except json.JSONDecodeError:
                    continue
    return ids


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False))
        fh.write("\n")


# ---------------------------------------------------------------------------
# Core labeling
# ---------------------------------------------------------------------------


async def _label_one(article: dict[str, Any], *, labeler: GeminiLabeler) -> dict[str, Any]:
    user_prompt = render_user_prompt(
        title=str(article.get("title") or ""),
        category=str(article.get("category") or ""),
        source=str(article.get("source") or ""),
        content_text=str(article.get("content_text") or ""),
    )
    try:
        raw = await asyncio.to_thread(
            labeler.generate, system=SYSTEM_PROMPT, user=user_prompt
        )
        output = parse_label_json(raw)
        qc = run_qc(
            output=output,
            source_text=f"{article.get('title') or ''} {article.get('content_text') or ''}",
        )
        return {
            **article,
            "summary": output.summary.strip(),
            "key_entities": output.key_entities,
            "confidence": output.confidence,
            "refusal_reason": output.refusal_reason,
            "prompt_version": PROMPT_VERSION,
            "qc_passed": qc.passed,
            "qc_details": qc.to_dict(),
        }
    except (GeminiLLMError, GeminiTransientError, ValueError) as exc:
        return {
            **article,
            "summary": "",
            "key_entities": [],
            "confidence": 0.0,
            "refusal_reason": str(exc),
            "prompt_version": PROMPT_VERSION,
            "qc_passed": False,
            "qc_details": {"passed": False, "reasons": [f"label_error:{exc}"]},
        }


async def batch_label(
    input_path: Path,
    output_path: Path,
    *,
    config: BatchConfig | None = None,
    api_keys: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Label articles with gemini-3.1-flash-lite using key rotation.

    - Resumable: skips already-labeled article_ids.
    - Writes incrementally so progress is never lost.
    - Rotates keys round-robin to spread RPD across projects.
    """
    config = config or BatchConfig()
    keys = api_keys or _keys_from_env()

    all_articles = read_jsonl(input_path)
    existing_ids = _load_existing_ids(output_path)
    pending = [a for a in all_articles if a.get("article_id") not in existing_ids]
    if limit is not None:
        pending = pending[:limit]

    if not pending:
        return {
            "model": MODEL,
            "total_articles": len(all_articles),
            "already_done": len(existing_ids),
            "processed_this_run": 0,
            "message": "Nothing to process — all articles already labeled.",
        }

    tracker = KeyUsageTracker(budget_per_key=config.max_per_key_per_day)
    processed = 0
    qc_passed = 0
    errors = 0
    start_time = time.time()
    current_key_idx = 0

    log.info(
        "Batch labeling: %d pending, %d keys, model=%s, delay=%.1fs",
        len(pending), len(keys), MODEL, config.delay_between_requests,
    )

    for article in pending:
        key_idx = tracker.get_next_available(len(keys), start=current_key_idx)
        if key_idx is None:
            log.warning("All keys exhausted daily budget. Stopping. Processed: %d", processed)
            break
        current_key_idx = (key_idx + 1) % len(keys)

        labeler = GeminiLabeler(
            api_keys=[keys[key_idx]],
            model_chain=[MODEL],
            params=GenerationParams(),
        )

        result = await _label_one(article, labeler=labeler)
        _append_jsonl(output_path, result)
        tracker.record_use(key_idx)
        processed += 1

        if result.get("qc_passed"):
            qc_passed += 1
        else:
            errors += 1

        if processed % 10 == 0:
            log.info(
                "Progress: %d/%d | qc_pass=%d | remaining=%d",
                processed, len(pending), qc_passed, tracker.total_remaining(len(keys)),
            )

        await asyncio.sleep(config.delay_between_requests)

    elapsed = time.time() - start_time
    daily_capacity = len(keys) * config.max_per_key_per_day

    return {
        "model": MODEL,
        "total_articles": len(all_articles),
        "already_done": len(existing_ids),
        "processed_this_run": processed,
        "qc_passed": qc_passed,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
        "avg_seconds_per_article": round(elapsed / max(processed, 1), 2),
        "remaining_key_capacity": tracker.total_remaining(len(keys)),
        "keys_used": len(keys),
        "daily_capacity": daily_capacity,
        "days_to_label_all": (len(all_articles) + daily_capacity - 1) // daily_capacity,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _keys_from_env() -> list[str]:
    raw = os.environ.get("GEMINI_API_KEYS", "").strip()
    if not raw:
        single = os.environ.get("GEMINI_API_KEY", "").strip()
        if single:
            return [single]
        raise GeminiLLMError("Set GEMINI_API_KEYS or GEMINI_API_KEY")
    return [k.strip() for k in raw.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch label articles with gemini-3.1-flash-lite"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None, help="Max articles to label")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--delay", type=float, default=SAFE_DELAY,
                        help=f"Seconds between requests (default: {SAFE_DELAY})")
    parser.add_argument("--max-per-key", type=int, default=SAFE_RPD_BUDGET,
                        help=f"Max requests per key per day (default: {SAFE_RPD_BUDGET})")
    return parser


async def _run_cli(args: argparse.Namespace) -> int:
    config = BatchConfig(
        batch_size=args.batch_size,
        delay_between_requests=args.delay,
        max_per_key_per_day=args.max_per_key,
    )
    summary = await batch_label(args.input, args.output, config=config, limit=args.limit)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("processed_this_run", 0) > 0 or summary.get("already_done", 0) > 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return asyncio.run(_run_cli(args))
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
