"""FastAPI web demo for the simplified Vietnamese news summarizer."""

from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.crawler import crawl_articles
from app.schemas import HealthResponse, SummarizeResponse, SummaryItem
from app.summarizer import ViT5Summarizer

APP_VERSION = "0.2.0-simple"

app = FastAPI(
    title="vn-news-summarizer",
    version=APP_VERSION,
    description="Vietnamese news summarization demo using RSS crawl + fine-tuned ViT5.",
)
templates = Jinja2Templates(directory="app/templates")
summarizer = ViT5Summarizer()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "model_id": summarizer.model_id,
            "max_articles": int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5")),
        },
    )


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)


@app.post("/api/summarize-today", response_model=SummarizeResponse)
async def summarize_today() -> SummarizeResponse:
    limit = int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5"))
    articles, _stats = await crawl_articles(mode="demo", limit=limit)
    if not articles:
        raise HTTPException(status_code=502, detail="No article could be crawled and extracted.")

    try:
        summaries = summarizer.summarize_batch([article.content_text for article in articles])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {exc}") from exc

    items = [
        SummaryItem(
            title=article.title,
            source=article.source_name,
            url=article.url,
            published_at=article.published_at,
            summary=summary,
        )
        for article, summary in zip(articles, summaries, strict=True)
    ]
    return SummarizeResponse(date=date.today().isoformat(), total=len(items), items=items)
