"""Simple RSS crawler used by both dataset building and the web demo.

The original project persisted crawl output to SQL tables. This module
keeps the proven crawl behavior but writes plain JSONL records instead:
RSS discovery, polite HTTP fetches, robots.txt checks, content
extraction, canonical URL dedupe, and SimHash near-duplicate filtering.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import sys
import time
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import feedparser
import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from simhash import Simhash
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.schemas import ArticleCandidate, CrawledArticle
from app.sources import (
    CRAWL_DELAY_SECONDS,
    MAX_RETRIES,
    TIMEOUT_SECONDS,
    USER_AGENT,
    CrawlStats,
    NewsSource,
    canonical_category,
    enabled_sources,
)

_WS_RE = re.compile(r"\s+")
_BOILERPLATE_RE = re.compile(
    r"(?im)^\s*(?:đọc thêm|doc them|xem thêm|xem them|tags?:|"
    r"từ khóa:|tu khoa:|liên quan:|lien quan:|chia sẻ|chia se).*$"
)
_CATEGORY_FROM_PATH_RE = re.compile(r"^/?([\w\-]+)/", re.IGNORECASE)
_SIMHASH_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fcc]+", re.UNICODE)
_SIMHASH_NGRAM_WIDTH = 4
_SIMHASH_WEIGHT_CAP = 50
_TRACKING_PREFIXES = (
    "utm_",
    "ga_",
    "yclid",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "vero_",
    "_ga",
    "ref",
    "ref_src",
    "ref_url",
    "spm",
    "share_source",
    "from",
    "src",
)


@dataclass(slots=True)
class ExtractedArticle:
    title: str | None
    author: str | None
    published_at: datetime | None
    language: str | None
    content_text: str
    word_count: int


class PoliteClient:
    """Small async HTTP client with per-host delay and retry."""

    def __init__(
        self,
        *,
        user_agent: str = USER_AGENT,
        timeout_s: float = TIMEOUT_SECONDS,
        crawl_delay_s: float = CRAWL_DELAY_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout_s,
            headers={"User-Agent": user_agent, "Accept-Language": "vi,en;q=0.7"},
            follow_redirects=True,
        )
        self._min_interval = max(crawl_delay_s, 0.0)
        self._last_by_host: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._max_retries = max_retries

    async def get(self, url: str) -> httpx.Response:
        host = urlsplit(url).netloc.lower()
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            if self._min_interval > 0:
                last = self._last_by_host.get(host, 0.0)
                wait_s = self._min_interval - (time.monotonic() - last)
                if wait_s > 0:
                    await asyncio.sleep(wait_s + random.uniform(0, 0.05))
            self._last_by_host[host] = time.monotonic()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=15),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                response = await self._client.get(url)
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"retryable status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                return response
        raise RuntimeError("unreachable")

    async def aclose(self) -> None:
        await self._client.aclose()


class RobotsCache:
    """robots.txt cache backed by the same async client style."""

    def __init__(self, *, user_agent: str = USER_AGENT, timeout_s: float = TIMEOUT_SECONDS) -> None:
        self.user_agent = user_agent
        self._client = httpx.AsyncClient(timeout=timeout_s, headers={"User-Agent": user_agent})
        self._cache: dict[str, RobotFileParser] = {}

    async def can_fetch(self, url: str) -> bool:
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if not host:
            return False
        parser = self._cache.get(host)
        if parser is None:
            robots_url = f"{parts.scheme or 'https'}://{host}/robots.txt"
            parser = RobotFileParser(robots_url)
            try:
                response = await self._client.get(robots_url)
                parser.parse(response.text.splitlines() if response.status_code < 400 else [])
            except httpx.HTTPError:
                parser.parse([])
            self._cache[host] = parser
        return parser.can_fetch(self.user_agent, url)

    async def aclose(self) -> None:
        await self._client.aclose()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = _BOILERPLATE_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    if (scheme == "http" and netloc.endswith(":80")) or (
        scheme == "https" and netloc.endswith(":443")
    ):
        netloc = netloc.rsplit(":", 1)[0]
    pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if not any(k.lower().startswith(prefix) for prefix in _TRACKING_PREFIXES)
    ]
    pairs.sort()
    path = parts.path or "/"
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((scheme, netloc, path, urlencode(pairs, doseq=True), ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()[:32]


def _simhash_features(text: str) -> dict[str, int]:
    joined = "".join(_SIMHASH_TOKEN_RE.findall(text.lower()))
    if not joined:
        return {}
    if len(joined) < _SIMHASH_NGRAM_WIDTH:
        return {joined: 1}
    counts = Counter(
        joined[i : i + _SIMHASH_NGRAM_WIDTH]
        for i in range(len(joined) - _SIMHASH_NGRAM_WIDTH + 1)
    )
    return {feature: min(weight, _SIMHASH_WEIGHT_CAP) for feature, weight in counts.items()}


def simhash64(text: str) -> int:
    features = _simhash_features(text)
    if not features:
        return 0
    value = int(Simhash(features, f=64).value) & ((1 << 64) - 1)
    if value >= (1 << 63):
        value -= 1 << 64
    return value


def hamming(a: int, b: int) -> int:
    return bin((a ^ b) & ((1 << 64) - 1)).count("1")


def _to_utc(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
    else:
        try:
            dt = parsedate_to_datetime(str(raw))
        except (TypeError, ValueError, IndexError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _category_from_url(url: str) -> str | None:
    try:
        path = url.split("//", 1)[1].split("/", 1)[1]
    except IndexError:
        return None
    match = _CATEGORY_FROM_PATH_RE.match(path)
    if not match:
        return None
    return match.group(1).replace("-", "_").lower()


async def fetch_feed(
    client: PoliteClient,
    *,
    source: NewsSource,
    feed_url: str,
) -> list[ArticleCandidate]:
    try:
        response = await client.get(feed_url)
    except Exception as exc:
        print(f"[crawler] RSS fetch failed {feed_url}: {exc}", file=sys.stderr)
        return []
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        print(f"[crawler] RSS parse failed {feed_url}: {parsed.bozo_exception}", file=sys.stderr)
        return []
    candidates: list[ArticleCandidate] = []
    for entry in parsed.entries:
        link = str(entry.get("link") or "")
        title = str(entry.get("title") or "").strip()
        if not link or not title:
            continue
        category = None
        if entry.get("tags"):
            category = entry["tags"][0].get("term") or None
        candidates.append(
            ArticleCandidate(
                source=source.id,
                source_name=source.name,
                url=canonicalize_url(link),
                title=normalize_text(title),
                published_at=_to_utc(
                    entry.get("published")
                    or entry.get("updated")
                    or entry.get("pubDate")
                    or entry.get("dc_date")
                ),
                category=canonical_category(category or _category_from_url(link)),
                author=(str(entry.get("author")) if entry.get("author") else None),
            )
        )
    return candidates


def extract_from_html(html: str, *, url: str | None = None) -> ExtractedArticle | None:
    if not html:
        return None
    try:
        extracted = trafilatura.extract(
            html,
            url=url,
            with_metadata=True,
            output_format="json",
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        if extracted:
            doc = json.loads(extracted)
            text = normalize_text(str(doc.get("text") or ""))
            if word_count(text) >= 50:
                return ExtractedArticle(
                    title=(str(doc.get("title")) if doc.get("title") else None),
                    author=(str(doc.get("author")) if doc.get("author") else None),
                    published_at=_to_utc(doc.get("date")),
                    language=(str(doc.get("language")) if doc.get("language") else None),
                    content_text=text,
                    word_count=word_count(text),
                )
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    try:
        doc = Document(html)
        soup = BeautifulSoup(doc.summary(), "lxml")
        text = normalize_text(soup.get_text(" "))
        if word_count(text) >= 50:
            return ExtractedArticle(
                title=doc.short_title() or None,
                author=None,
                published_at=None,
                language=None,
                content_text=text,
                word_count=word_count(text),
            )
    except Exception:
        pass
    return None


async def crawl_articles(
    *,
    mode: str = "labeling",
    limit: int | None = None,
    only_sources: Iterable[str] | None = None,
) -> tuple[list[CrawledArticle], dict[str, CrawlStats]]:
    """Crawl articles into memory.

    ``mode`` controls the default limit only. ``labeling`` consumes the
    configured RSS caps, while ``demo`` stops after a small number of
    successfully extracted articles unless the caller supplies a limit.
    """
    selected = set(only_sources or []) or None
    sources = enabled_sources(selected)
    target = limit if limit is not None else (5 if mode == "demo" else None)
    client = PoliteClient()
    robots = RobotsCache()
    seen_urls: set[str] = set()
    seen_hashes: list[int] = []
    articles: list[CrawledArticle] = []
    stats_by_source: dict[str, CrawlStats] = {source.id: CrawlStats() for source in sources}

    try:
        for source in sources:
            stats = stats_by_source[source.id]
            # Always print a one-line progress marker per source so the CLI
            # doesn't look stuck on large RSS lists.
            print(f"[crawler] source={source.id} feeds={len(source.rss)}", file=sys.stderr)
            candidates: list[ArticleCandidate] = []
            for feed_url in source.rss:
                feed_items = await fetch_feed(client, source=source, feed_url=feed_url)
                if source.max_items_per_feed is not None:
                    feed_items = feed_items[: source.max_items_per_feed]
                candidates.extend(feed_items)
            stats.discovered = len(candidates)
            print(f"[crawler] source={source.id} discovered={stats.discovered}", file=sys.stderr)

            for candidate in candidates:
                if target is not None and len(articles) >= target:
                    return articles, stats_by_source
                canonical_url = canonicalize_url(candidate.url)
                if canonical_url in seen_urls:
                    stats.skipped_duplicate += 1
                    continue
                seen_urls.add(canonical_url)
                if not await robots.can_fetch(canonical_url):
                    stats.skipped_robots += 1
                    continue
                try:
                    response = await client.get(canonical_url)
                    stats.fetched += 1
                except Exception as exc:
                    stats.fetch_failed += 1
                    stats.errors.append(f"{canonical_url}: {exc}")
                    continue

                extracted = extract_from_html(response.text, url=canonical_url)
                if extracted is None:
                    stats.extract_failed += 1
                    continue
                simhash_value = simhash64(extracted.content_text)
                if any(hamming(simhash_value, existing) <= 3 for existing in seen_hashes):
                    stats.skipped_duplicate += 1
                    continue
                seen_hashes.append(simhash_value)
                stats.extracted += 1
                published = extracted.published_at or candidate.published_at
                record = CrawledArticle(
                    article_id=len(articles) + 1,
                    source=source.id,
                    source_name=source.name,
                    url=canonical_url,
                    title=normalize_text(extracted.title or candidate.title),
                    category=candidate.category,
                    published_at=published.isoformat() if published else None,
                    author=extracted.author or candidate.author,
                    content_text=extracted.content_text,
                    word_count=extracted.word_count,
                    url_hash=url_hash(canonical_url),
                )
                articles.append(record)
                if stats.extracted % 5 == 0:
                    print(
                        f"[crawler] source={source.id} extracted={stats.extracted} total={len(articles)}",
                        file=sys.stderr,
                    )
    finally:
        await client.aclose()
        await robots.aclose()
    return articles, stats_by_source


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")


def _validate_cli_output_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    raw = str(path)
    if "/" in raw or "\\" in raw:
        return path
    if raw.lower().endswith(".jsonl") and raw.lower().startswith("data"):
        raise ValueError(
            "Output path looks flattened by the shell: "
            f"{raw!r}. On Windows shells that treat backslash as an escape, "
            "use forward slashes like data/raw/articles.jsonl or quote the path."
        )
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simplified RSS crawler")
    parser.add_argument("--mode", choices=["labeling", "demo"], default="labeling")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--source", action="append", default=None)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress while crawling (useful for long labeling crawls).",
    )
    return parser


async def _run_cli(args: argparse.Namespace) -> int:
    try:
        output_path = _validate_cli_output_path(args.output)
    except ValueError as exc:
        print(f"[crawler] {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        print(
            f"[crawler] mode={args.mode} limit={args.limit} output={output_path}",
            file=sys.stderr,
        )

    articles, stats = await crawl_articles(
        mode=args.mode,
        limit=args.limit,
        only_sources=args.source,
    )
    rows = [article.to_jsonl_record() for article in articles]
    if output_path:
        write_jsonl(output_path, rows)
        print(f"[crawler] wrote {len(rows)} articles to {output_path}")
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    for source_id, source_stats in stats.items():
        if args.verbose or source_stats.errors:
            print(f"[crawler] {source_id}: {source_stats}", file=sys.stderr)
    return 0 if articles else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_run_cli(args))


if __name__ == "__main__":
    raise SystemExit(main())
