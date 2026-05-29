"""Label crawled JSONL articles with Gemini (AI Studio) and deterministic QC."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from labeling.gemini_labeler import GeminiLabeler, GeminiLLMError, GeminiTransientError
from labeling.io import read_jsonl, write_jsonl
from labeling.prompt import (
    PROMPT_MODEL,
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    GenerationParams,
    parse_label_json,
    render_user_prompt,
)
from labeling.qc import run_qc


async def _label_one(
    row: dict[str, Any],
    *,
    labeler: GeminiLabeler,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    user_prompt = render_user_prompt(
        title=str(row.get("title") or ""),
        category=str(row.get("category") or ""),
        source=str(row.get("source") or ""),
        content_text=str(row.get("content_text") or ""),
    )
    try:
        async with semaphore:
            raw = await asyncio.to_thread(labeler.generate, system=SYSTEM_PROMPT, user=user_prompt)
        output = parse_label_json(raw)
        qc = run_qc(
            output=output,
            source_text=f"{row.get('title') or ''} {row.get('content_text') or ''}",
        )
        return {
            **row,
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
            **row,
            "summary": "",
            "key_entities": [],
            "confidence": 0.0,
            "refusal_reason": str(exc),
            "prompt_version": PROMPT_VERSION,
            "qc_passed": False,
            "qc_details": {"passed": False, "reasons": [f"label_error:{exc}"]},
        }


async def label_rows(
    rows: list[dict[str, Any]],
    *,
    concurrency: int = 5,
    limit: int | None = None,
    labeler: GeminiLabeler | None = None,
) -> list[dict[str, Any]]:
    if labeler is None:
        labeler = GeminiLabeler(params=GenerationParams())
    semaphore = asyncio.Semaphore(max(concurrency, 1))
    work = rows[:limit] if limit is not None else rows
    tasks = [_label_one(row, labeler=labeler, semaphore=semaphore) for row in work]
    return list(await asyncio.gather(*tasks))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Label crawled articles with Gemini")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=5)
    return parser


async def _run_cli(args: argparse.Namespace) -> int:
    rows = read_jsonl(args.input)
    labeled = await label_rows(
        rows, concurrency=args.concurrency, limit=args.limit
    )
    write_jsonl(args.output, labeled)
    passed = sum(1 for row in labeled if row.get("qc_passed") is True)
    print(
        f"labeled={len(labeled)} qc_passed={passed} qc_failed={len(labeled) - passed} "
        f"prompt={PROMPT_VERSION} model={PROMPT_MODEL}"
    )
    return 0 if labeled else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return asyncio.run(_run_cli(args))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
