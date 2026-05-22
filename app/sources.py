"""RSS sources frozen from the repo's RSS fix commit.

This replaces the previous YAML-driven source config for the simplified
runtime, but keeps the exact operational choices that produced the v2
labeling corpus: Lao Dong disabled and VietnamNet capped at 100 items
per feed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


USER_AGENT = "vn-news-summarizer-research/0.1 (+https://github.com/khangnh22ds/vn-news-summarizer)"
CRAWL_DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = 20.0
MAX_RETRIES = 3


@dataclass(slots=True, frozen=True)
class NewsSource:
    id: str
    name: str
    domain: str
    rss: list[str]
    enabled: bool = True
    max_items_per_feed: int | None = None


SOURCES: list[NewsSource] = [
    NewsSource(
        id="vnexpress",
        name="VnExpress",
        domain="vnexpress.net",
        rss=[
            "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "https://vnexpress.net/rss/thoi-su.rss",
            "https://vnexpress.net/rss/kinh-doanh.rss",
            "https://vnexpress.net/rss/so-hoa.rss",
            "https://vnexpress.net/rss/the-thao.rss",
            "https://vnexpress.net/rss/giai-tri.rss",
            "https://vnexpress.net/rss/giao-duc.rss",
            "https://vnexpress.net/rss/khoa-hoc.rss",
            "https://vnexpress.net/rss/suc-khoe.rss",
        ],
    ),
    NewsSource(
        id="tuoitre",
        name="Tuoi Tre Online",
        domain="tuoitre.vn",
        rss=[
            "https://tuoitre.vn/rss/tin-moi-nhat.rss",
            "https://tuoitre.vn/rss/thoi-su.rss",
            "https://tuoitre.vn/rss/kinh-doanh.rss",
            "https://tuoitre.vn/rss/cong-nghe.rss",
            "https://tuoitre.vn/rss/the-thao.rss",
            "https://tuoitre.vn/rss/giai-tri.rss",
            "https://tuoitre.vn/rss/giao-duc.rss",
            "https://tuoitre.vn/rss/suc-khoe.rss",
        ],
    ),
    NewsSource(
        id="thanhnien",
        name="Thanh Nien",
        domain="thanhnien.vn",
        rss=[
            "https://thanhnien.vn/rss/home.rss",
            "https://thanhnien.vn/rss/thoi-su.rss",
            "https://thanhnien.vn/rss/kinh-te.rss",
            "https://thanhnien.vn/rss/cong-nghe.rss",
            "https://thanhnien.vn/rss/the-thao.rss",
            "https://thanhnien.vn/rss/giai-tri.rss",
            "https://thanhnien.vn/rss/giao-duc.rss",
            "https://thanhnien.vn/rss/suc-khoe.rss",
        ],
    ),
    NewsSource(
        id="vietnamnet",
        name="VietnamNet",
        domain="vietnamnet.vn",
        max_items_per_feed=100,
        rss=[
            "https://vietnamnet.vn/rss/thoi-su.rss",
            "https://vietnamnet.vn/rss/kinh-doanh.rss",
            "https://vietnamnet.vn/rss/cong-nghe.rss",
            "https://vietnamnet.vn/rss/the-thao.rss",
            "https://vietnamnet.vn/rss/giai-tri.rss",
            "https://vietnamnet.vn/rss/giao-duc.rss",
            "https://vietnamnet.vn/rss/suc-khoe.rss",
        ],
    ),
    NewsSource(
        id="dantri",
        name="Dan Tri",
        domain="dantri.com.vn",
        rss=[
            "https://dantri.com.vn/rss/home.rss",
            "https://dantri.com.vn/rss/xa-hoi.rss",
            "https://dantri.com.vn/rss/kinh-doanh.rss",
            "https://dantri.com.vn/rss/cong-nghe.rss",
            "https://dantri.com.vn/rss/the-thao.rss",
            "https://dantri.com.vn/rss/giai-tri.rss",
            "https://dantri.com.vn/rss/giao-duc-huong-nghiep.rss",
            "https://dantri.com.vn/rss/suc-khoe.rss",
        ],
    ),
    NewsSource(
        id="znews",
        name="Znews",
        domain="znews.vn",
        rss=[
            "https://znews.vn/rss/thoi-su.rss",
            "https://znews.vn/rss/xa-hoi.rss",
            "https://znews.vn/rss/cong-nghe.rss",
            "https://znews.vn/rss/the-thao.rss",
            "https://znews.vn/rss/giai-tri.rss",
            "https://znews.vn/rss/giao-duc.rss",
            "https://znews.vn/rss/suc-khoe.rss",
            "https://znews.vn/rss/the-gioi.rss",
        ],
    ),
    NewsSource(
        id="vtcnews",
        name="VTC News",
        domain="vtcnews.vn",
        rss=[
            "https://vtcnews.vn/rss/feed.rss",
            "https://vtcnews.vn/rss/thoi-su.rss",
            "https://vtcnews.vn/rss/kinh-te.rss",
            "https://vtcnews.vn/rss/cong-nghe.rss",
            "https://vtcnews.vn/rss/the-thao.rss",
            "https://vtcnews.vn/rss/giai-tri.rss",
        ],
    ),
    NewsSource(
        id="laodong",
        name="Lao Dong",
        domain="laodong.vn",
        enabled=False,
        rss=[
            "https://laodong.vn/rss/home.rss",
            "https://laodong.vn/rss/thoi-su.rss",
            "https://laodong.vn/rss/kinh-doanh.rss",
            "https://laodong.vn/rss/cong-nghe.rss",
            "https://laodong.vn/rss/the-thao.rss",
            "https://laodong.vn/rss/van-hoa-giai-tri.rss",
            "https://laodong.vn/rss/giao-duc.rss",
            "https://laodong.vn/rss/suc-khoe.rss",
        ],
    ),
]


CANONICAL_CATEGORIES: dict[str, list[str]] = {
    "thoi_su": ["thời sự", "thoi su", "thoi-su", "thoi_su", "xã hội", "xa-hoi", "xa_hoi", "xa hoi"],
    "kinh_doanh": ["kinh doanh", "kinh-doanh", "kinh_doanh", "kinh tế", "kinh-te", "kinh_te", "kinh te"],
    "cong_nghe": ["công nghệ", "cong nghe", "cong-nghe", "cong_nghe", "so-hoa", "so_hoa", "khoa-hoc", "khoa_hoc"],
    "the_thao": ["thể thao", "the thao", "the-thao", "the_thao"],
    "giai_tri": ["giải trí", "giai tri", "giai-tri", "giai_tri", "van-hoa-giai-tri", "van_hoa_giai_tri"],
    "giao_duc": ["giáo dục", "giao duc", "giao-duc", "giao_duc", "giao-duc-huong-nghiep", "giao_duc_huong_nghiep"],
    "suc_khoe": ["sức khỏe", "suc khoe", "suc-khoe", "suc_khoe"],
    "the_gioi": ["thế giới", "the gioi", "the-gioi", "the_gioi"],
}


@dataclass(slots=True)
class CrawlStats:
    discovered: int = 0
    fetched: int = 0
    extracted: int = 0
    skipped_duplicate: int = 0
    skipped_robots: int = 0
    fetch_failed: int = 0
    extract_failed: int = 0
    errors: list[str] = field(default_factory=list)


def enabled_sources(only: set[str] | None = None) -> list[NewsSource]:
    return [s for s in SOURCES if s.enabled and (only is None or s.id in only)]


def canonical_category(raw: str | None) -> str | None:
    if not raw:
        return None
    needle = raw.lower()
    for key, aliases in CANONICAL_CATEGORIES.items():
        if any(alias in needle or needle in alias for alias in aliases):
            return key
    return None
