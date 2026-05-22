"""Shared data shapes for crawl, labeling, and API responses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class ArticleCandidate:
    source: str
    source_name: str
    url: str
    title: str
    published_at: datetime | None = None
    category: str | None = None
    author: str | None = None


@dataclass(slots=True, frozen=True)
class CrawledArticle:
    article_id: int
    source: str
    source_name: str
    url: str
    title: str
    category: str | None
    published_at: str | None
    author: str | None
    content_text: str
    word_count: int
    url_hash: str

    def to_jsonl_record(self) -> dict[str, object]:
        return {
            "article_id": self.article_id,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "category": self.category,
            "published_at": self.published_at,
            "content_text": self.content_text,
        }


class SummaryItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: str | None = None
    summary: str


class SummarizeResponse(BaseModel):
    date: str
    total: int = Field(ge=0)
    items: list[SummaryItem]


class HealthResponse(BaseModel):
    status: str
    version: str
