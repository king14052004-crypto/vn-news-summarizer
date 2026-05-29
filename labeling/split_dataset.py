"""Export QC-passed labels to deterministic train/val/test JSONL splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from labeling.io import read_jsonl, write_jsonl

SplitName = Literal["train", "val", "test"]
EXPECTED_V2_COUNTS = {"train": 1636, "val": 218, "test": 216}


def split_bucket(article_id: int, *, salt: str = "vn-news-v1") -> SplitName:
    digest = hashlib.sha256(f"{salt}:{article_id}".encode()).digest()
    bucket = digest[0]
    if bucket < 26:
        return "test"
    if bucket < 52:
        return "val"
    return "train"


def dataset_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "article_id": int(row.get("article_id") or 0),
        "source": str(row.get("source") or ""),
        "url": str(row.get("url") or ""),
        "title": str(row.get("title") or ""),
        "category": row.get("category"),
        "published_at": row.get("published_at"),
        "content_text": str(row.get("content_text") or ""),
        "summary": str(row.get("summary") or ""),
        "prompt_version": str(row.get("prompt_version") or ""),
    }


def split_rows(rows: list[dict[str, Any]]) -> dict[SplitName, list[dict[str, Any]]]:
    splits: dict[SplitName, list[dict[str, Any]]] = {"train": [], "val": [], "test": []}
    for row in rows:
        if row.get("qc_passed") is False:
            continue
        record = dataset_record(row)
        if not record["content_text"] or not record["summary"]:
            continue
        splits[split_bucket(int(record["article_id"]))].append(record)
    return splits


def export_splits(input_path: Path, output_dir: Path) -> dict[str, int]:
    rows = read_jsonl(input_path)
    splits = split_rows(rows)
    for split, split_rows_ in splits.items():
        write_jsonl(output_dir / f"{split}.jsonl", split_rows_)
    return {split: len(split_rows_) for split, split_rows_ in splits.items()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build deterministic dataset splits")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--check-v2-counts",
        action="store_true",
        help="Fail unless split counts match the historical v2 report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    counts = export_splits(args.input, args.output)
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    if args.check_v2_counts and counts != EXPECTED_V2_COUNTS:
        print(f"expected v2 counts {EXPECTED_V2_COUNTS}, got {counts}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
