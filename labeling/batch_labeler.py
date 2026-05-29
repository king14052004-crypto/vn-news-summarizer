"""Batch labeling with gemini-3.1-flash-lite and multi-key rotation.

Free-tier limits (gemini-3.1-flash-lite):
    15 RPM  |  500 RPD/project  |  250K TPM

Strategy:
    - Delay 4.5s between requests → safe for 15 RPM
    - Rotate keys round-robin → spread RPD across projects
    - Write results incrementally → resumable on crash
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from labeling.gemini_labeler import GeminiLabeler, GeminiLLMError, GeminiTransientError, _keys_from_env
from labeling.io import read_jsonl
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
DELAY = 4.5           # seconds between requests (safe for 15 RPM)
MAX_PER_KEY = 450     # conservative daily budget per key (< 500 RPD)


def _load_done_ids(path: Path) -> set[int]:
    """Load article_ids already in output file (for resume)."""
    if not path.exists():
        return set()
    ids: set[int] = set()
    with path.open("r", encoding="utf-8") as fh:
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
    """Append one JSON row to file (incremental write)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Core labeling
# ---------------------------------------------------------------------------


async def _label_one(article: dict[str, Any], labeler: GeminiLabeler) -> dict[str, Any]:
    """Label a single article. Returns result dict (never raises)."""
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
    api_keys: list[str] | None = None,
    limit: int | None = None,
    delay: float = DELAY,
    max_per_key: int = MAX_PER_KEY,
) -> dict[str, Any]:
    """Label articles sequentially with key rotation.

    - Resumable: skips article_ids already in output file.
    - Incremental: writes each result immediately.
    - Round-robin: rotates keys to spread daily quota.
    """
    keys = api_keys or _keys_from_env()

    all_articles = read_jsonl(input_path)
    done_ids = _load_done_ids(output_path)
    pending = [a for a in all_articles if a.get("article_id") not in done_ids]
    if limit is not None:
        pending = pending[:limit]

    if not pending:
        log.info("Nothing to process — all articles already labeled.")
        return {"processed": 0, "already_done": len(done_ids)}

    # Track usage per key: counts[i] = requests used by key i
    counts = [0] * len(keys)
    current = 0
    processed = 0
    qc_passed = 0
    start = time.time()

    log.info("Batch: %d pending, %d keys, model=%s, delay=%.1fs",
             len(pending), len(keys), MODEL, delay)

    for article in pending:
        # Find next key with budget remaining (round-robin)
        key_idx = None
        for _ in range(len(keys)):
            if counts[current] < max_per_key:
                key_idx = current
                current = (current + 1) % len(keys)
                break
            current = (current + 1) % len(keys)

        if key_idx is None:
            log.warning("All keys exhausted daily budget. Stopping.")
            break

        labeler = GeminiLabeler(
            api_keys=[keys[key_idx]],
            model_chain=[MODEL],
            params=GenerationParams(),
        )
        result = await _label_one(article, labeler)
        _append_jsonl(output_path, result)
        counts[key_idx] += 1
        processed += 1

        if result.get("qc_passed"):
            qc_passed += 1

        if processed % 10 == 0:
            remaining = sum(max_per_key - c for c in counts)
            log.info("Progress: %d/%d | qc_pass=%d | remaining=%d",
                     processed, len(pending), qc_passed, remaining)

        await asyncio.sleep(delay)

    elapsed = time.time() - start
    return {
        "model": MODEL,
        "total": len(all_articles),
        "already_done": len(done_ids),
        "processed": processed,
        "qc_passed": qc_passed,
        "elapsed_s": round(elapsed, 1),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch label with gemini-3.1-flash-lite")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=DELAY)
    parser.add_argument("--max-per-key", type=int, default=MAX_PER_KEY)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    async def _run() -> int:
        summary = await batch_label(
            args.input, args.output,
            limit=args.limit, delay=args.delay, max_per_key=args.max_per_key,
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0 if summary.get("processed", 0) > 0 or summary.get("already_done", 0) > 0 else 1

    try:
        return asyncio.run(_run())
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
