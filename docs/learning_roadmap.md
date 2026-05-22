# Lộ Trình Học Để Tự Code Lại `vn-news-summarizer`

Tài liệu này dành cho người mới học. Mục tiêu: hiểu từng mảnh nhỏ rồi **tự code lại được toàn bộ dự án**, từng file, từng dòng.

**Nguyên tắc:**
- Mỗi chặng dạy một nhóm kiến thức.
- Có bài tập nhỏ (có lời giải) giúp bạn nắm kiến thức.
- **Bài cuối chặng = code lại file .py thật trong dự án.** Nếu file đó dùng kiến thức từ chặng trước, bài cuối yêu cầu code lại toàn bộ file (tích lũy kiến thức).
- Cuối lộ trình bạn có thể code lại 100% dự án.

**Danh sách file trong dự án (theo thứ tự học):**

| File | Dòng | Chặng học |
|------|------|-----------|
| `app/schemas.py` | 64 | 1 |
| `app/sources.py` | 189 | 2 |
| `labeling/prompt.py` | 105 | 3 |
| `labeling/qc.py` | 153 | 4 |
| `labeling/gemini_labeler.py` | 182 | 5 |
| `labeling/label_dataset.py` | 133 | 6 |
| `labeling/split_dataset.py` | 100 | 7 |
| `app/crawler.py` | 514 | 8-9 |
| `app/summarizer.py` | 138 | 10 |
| `app/main.py` | 66 | 11 |
| `app/templates/index.html` | 140 | 11 |

---

## Chặng 0 — Nền Tảng Python

**Mục tiêu:** nắm vững cú pháp Python cần dùng trong dự án.

### Lý thuyết

**1. Module và package:**
- File `.py` = module. Thư mục có `__init__.py` = package.
- `from app.schemas import ArticleCandidate` → Python tìm `app/schemas.py`, lấy class `ArticleCandidate`.
- `__init__.py` có thể rỗng, chỉ cần tồn tại để Python nhận thư mục là package.

**2. Type hints:**
- `def word_count(text: str) -> int:` — tham số `text` kiểu `str`, trả về `int`.
- `str | None` = có thể là `str` hoặc `None`.
- `list[str]` = danh sách các chuỗi.
- `dict[str, Any]` = dict key là `str`, value là bất kỳ.
- `from __future__ import annotations` — cho phép dùng `str | None` thay vì `Optional[str]` trên Python < 3.10.

**3. f-string:**
- `f"Đã crawl {count} bài"` — chèn biến `count` vào chuỗi.

**4. Đọc/ghi JSONL:**
```python
import json
from pathlib import Path

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")
```

**Tại sao `ensure_ascii=False`?** Vì dữ liệu tiếng Việt. Nếu `True`, "Hà Nội" → `"H\\u00e0 N\\u1ed9i"`.

**5. `pathlib.Path`:**
```python
from pathlib import Path
p = Path("data/raw/articles.jsonl")
p.parent  # Path("data/raw")
p.parent.mkdir(parents=True, exist_ok=True)  # tạo thư mục nếu chưa có
p.open("r", encoding="utf-8")  # mở file
```

**6. argparse (CLI):**
```python
import argparse

parser = argparse.ArgumentParser(description="My tool")
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--limit", type=int, default=None)
args = parser.parse_args()
print(args.input, args.limit)
```

**7. Biến môi trường:**
```python
import os
value = os.environ.get("GEMINI_API_KEYS", "").strip()
# Trả "" nếu biến không tồn tại
```

### Bài tập 0.1 — Đọc ghi JSONL

**Yêu cầu:** Viết 2 function `read_jsonl(path)` và `write_jsonl(path, rows)` hoạt động như trên. Test:

```python
from pathlib import Path
rows = [{"title": "Tin A", "content": "Nội dung A"}, {"title": "Tin B", "content": "Nội dung B"}]
write_jsonl(Path("/tmp/test.jsonl"), rows)
loaded = read_jsonl(Path("/tmp/test.jsonl"))
assert loaded == rows
```

### Bài tập 0.2 — argparse CLI đọc JSONL

**Yêu cầu:** Viết CLI nhận `--input` (Path, required) và `--limit` (int, optional). Đọc JSONL, in `limit` dòng đầu (hoặc tất cả nếu không có limit).

**Đáp án:**

```python
import argparse, json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    rows = []
    with args.input.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    for row in rows[:args.limit]:
        print(json.dumps(row, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### Bài tập 0.3 — Biến môi trường

**Yêu cầu:** Viết function `get_keys()` đọc `GEMINI_API_KEYS` (comma-separated) hoặc `GEMINI_API_KEY` (single). Nếu cả hai đều không có, raise `RuntimeError`.

**Đáp án:**

```python
import os

def get_keys() -> list[str]:
    raw = os.environ.get("GEMINI_API_KEYS", "").strip()
    if raw:
        return [k.strip() for k in raw.split(",") if k.strip()]
    single = os.environ.get("GEMINI_API_KEY", "").strip()
    if single:
        return [single]
    raise RuntimeError("Set GEMINI_API_KEYS or GEMINI_API_KEY")
```

**So sánh dự án:** Mở `labeling/gemini_labeler.py`, function `_keys_from_env()` — logic giống hệt.

---

## Chặng 1 — Data Schemas (`app/schemas.py`)

**Mục tiêu:** hiểu `dataclass`, `Pydantic BaseModel`, `slots=True`, `frozen=True`. Code lại `app/schemas.py`.

### Lý thuyết

**1. `dataclass`:**
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
```
Python tự tạo `__init__`, `__repr__`, `__eq__`.

**2. `slots=True`:** tiết kiệm bộ nhớ, không cho thêm attribute mới ngoài khai báo.
```python
@dataclass(slots=True)
class Person:
    name: str
```
`Person("A").x = 1` → `AttributeError`.

**3. `frozen=True`:** immutable, không cho sửa attribute sau khi tạo.
```python
@dataclass(slots=True, frozen=True)
class Point:
    x: int
    y: int
```
`Point(1, 2).x = 3` → `FrozenInstanceError`.

**4. Pydantic `BaseModel`:**
```python
from pydantic import BaseModel, Field

class SummaryItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: str | None = None
    summary: str
```
- Tự validate type khi tạo: `SummaryItem(title=123, ...)` → tự ép thành `"123"` hoặc raise `ValidationError`.
- `Field(ge=0)` = giá trị >= 0.

**5. Khi nào dùng `dataclass` vs `BaseModel`?**
- `dataclass`: dữ liệu nội bộ, không cần validate từ bên ngoài (user input, JSON).
- `BaseModel`: dữ liệu từ bên ngoài (API response, JSON từ LLM) cần validate.

### Bài tập 1.1 — dataclass cơ bản

**Yêu cầu:** Tạo `ArticleCandidate` với:
- `source: str`, `source_name: str`, `url: str`, `title: str`
- `published_at: datetime | None = None`, `category: str | None = None`, `author: str | None = None`
- `slots=True, frozen=True`

**Đáp án:**

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True, frozen=True)
class ArticleCandidate:
    source: str
    source_name: str
    url: str
    title: str
    published_at: datetime | None = None
    category: str | None = None
    author: str | None = None
```

### Bài tập 1.2 — dataclass với method

**Yêu cầu:** Tạo `CrawledArticle` có method `to_jsonl_record()` trả dict chỉ gồm `article_id, source, url, title, category, published_at, content_text`.

**Đáp án:**

```python
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
```

### Bài tập 1.3 — Pydantic BaseModel

**Yêu cầu:** Tạo `SummaryItem`, `SummarizeResponse`, `HealthResponse` dùng Pydantic.

**Đáp án:**

```python
from pydantic import BaseModel, Field

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
```

### 🎯 Bài cuối chặng 1 — Code lại `app/schemas.py`

**Yêu cầu:** Tạo file `app/schemas.py` (64 dòng) chứa đầy đủ:
- `from __future__ import annotations`
- `ArticleCandidate` (dataclass, frozen, slots) — 7 fields
- `CrawledArticle` (dataclass, frozen, slots) — 11 fields + `to_jsonl_record()`
- `SummaryItem` (BaseModel) — 5 fields
- `SummarizeResponse` (BaseModel) — `date`, `total` (Field ge=0), `items`
- `HealthResponse` (BaseModel) — `status`, `version`

**Kiểm tra:** So với `app/schemas.py` trong dự án — phải giống 100%.

---

## Chặng 2 — Source Config (`app/sources.py`)

**Mục tiêu:** hiểu frozen config pattern, dict-based normalization, `field(default_factory=list)`. Code lại `app/sources.py`.

### Lý thuyết

**1. Config dạng frozen dataclass:**
Thay vì YAML/JSON, dự án "đóng băng" cấu hình RSS nguồn báo thành Python code. Lý do: đơn giản, type-safe, không cần đọc file.

```python
@dataclass(slots=True, frozen=True)
class NewsSource:
    id: str
    name: str
    domain: str
    rss: list[str]
    enabled: bool = True
    max_items_per_feed: int | None = None
```

**2. Category normalization:**
Mỗi báo gọi chuyên mục khác nhau ("thời sự" vs "thoi-su" vs "xa-hoi"). Dự án map tất cả về một tên chuẩn:

```python
CANONICAL_CATEGORIES = {
    "thoi_su": ["thời sự", "thoi su", "thoi-su", "xa-hoi", ...],
    "kinh_doanh": ["kinh doanh", "kinh-doanh", "kinh tế", ...],
    ...
}

def canonical_category(raw: str | None) -> str | None:
    if not raw:
        return None
    needle = raw.lower()
    for key, aliases in CANONICAL_CATEGORIES.items():
        if any(alias in needle or needle in alias for alias in aliases):
            return key
    return None
```

**3. `field(default_factory=list)`:**
Khi default value là mutable (list, dict), phải dùng `default_factory`:
```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class CrawlStats:
    discovered: int = 0
    errors: list[str] = field(default_factory=list)
```
Nếu viết `errors: list[str] = []` → tất cả instance chia sẻ cùng list (bug).

**4. Constants:**
```python
USER_AGENT = "vn-news-summarizer-research/0.1 (...)"
CRAWL_DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = 20.0
MAX_RETRIES = 3
```

### Bài tập 2.1 — NewsSource dataclass

**Yêu cầu:** Tạo `NewsSource` và `SOURCES` list chứa ít nhất 2 nguồn báo (VnExpress, Tuoi Tre) với RSS URLs thật.

**Đáp án:**

```python
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class NewsSource:
    id: str
    name: str
    domain: str
    rss: list[str]
    enabled: bool = True
    max_items_per_feed: int | None = None

SOURCES = [
    NewsSource(
        id="vnexpress", name="VnExpress", domain="vnexpress.net",
        rss=["https://vnexpress.net/rss/tin-moi-nhat.rss", "https://vnexpress.net/rss/thoi-su.rss"],
    ),
    NewsSource(
        id="tuoitre", name="Tuoi Tre Online", domain="tuoitre.vn",
        rss=["https://tuoitre.vn/rss/tin-moi-nhat.rss"],
    ),
]
```

### Bài tập 2.2 — canonical_category

**Yêu cầu:** Viết `canonical_category(raw)` và test:

```python
assert canonical_category("thời sự") == "thoi_su"
assert canonical_category("kinh-doanh") == "kinh_doanh"
assert canonical_category("xa-hoi") == "thoi_su"
assert canonical_category(None) is None
assert canonical_category("unknown") is None
```

### Bài tập 2.3 — CrawlStats và enabled_sources

**Yêu cầu:** Tạo `CrawlStats` dataclass (dùng `field(default_factory=list)` cho `errors`) và `enabled_sources(only)` function.

**Đáp án:**

```python
from dataclasses import dataclass, field

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
```

### 🎯 Bài cuối chặng 2 — Code lại `app/sources.py`

**Yêu cầu:** Tạo file `app/sources.py` (189 dòng) chứa đầy đủ:
- `USER_AGENT`, `CRAWL_DELAY_SECONDS`, `TIMEOUT_SECONDS`, `MAX_RETRIES`
- `NewsSource` dataclass (frozen, slots)
- `SOURCES` list — 8 nguồn báo (vnexpress, tuoitre, thanhnien, vietnamnet, dantri, znews, vtcnews, laodong)
  - `laodong` có `enabled=False`
  - `vietnamnet` có `max_items_per_feed=100`
- `CANONICAL_CATEGORIES` dict — 8 categories
- `CrawlStats` dataclass (slots, mutable)
- `enabled_sources(only)` function
- `canonical_category(raw)` function

**Kiểm tra:** So với `app/sources.py` trong dự án — phải giống 100%.

---

## Chặng 3 — Prompt & JSON Parser (`labeling/prompt.py`)

**Mục tiêu:** hiểu prompt engineering, Pydantic validation, robust JSON parsing. Code lại `labeling/prompt.py`.

### Lý thuyết

**1. Prompt design cho labeling:**
- System prompt: quy tắc chung cho AI (văn phong, độ dài, trung thực).
- User prompt: dữ liệu cụ thể (tiêu đề, nội dung bài báo).
- Output schema: JSON format cố định.

```python
SYSTEM_PROMPT = """Bạn là biên tập viên báo chí tiếng Việt. Tóm tắt phải:
- Trung thực 100% với bài gốc...
- 2-3 câu, 40-70 từ...
""".strip()

USER_TEMPLATE = """
Tiêu đề: {title}
Chuyên mục: {category}
...
Trả về JSON đúng schema:
{{"summary": "...", "key_entities": ["..."], "confidence": 0.0, "refusal_reason": null}}
""".strip()
```

**2. `GenerationParams`:** cấu hình gửi kèm mỗi request tới Gemini.
```python
@dataclass(slots=True)
class GenerationParams:
    temperature: float = 0.2       # thấp → output ổn định
    top_p: float = 0.9
    max_output_tokens: int = 4096
    response_mime_type: str = "application/json"  # bắt Gemini trả JSON
```

**3. `QcConfig`:** ngưỡng cho QC checks.

**4. `LabelOutput`:** Pydantic model validate output từ Gemini.
```python
class LabelOutput(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    refusal_reason: str | None = None
```

**5. `render_user_prompt`:** ghép dữ liệu vào template, cắt content tối đa 6000 ký tự (tránh tốn token).
```python
def render_user_prompt(*, title, category, source, content_text, content_max_chars=6000):
    snippet = content_text or ""
    if len(snippet) > content_max_chars:
        snippet = snippet[:content_max_chars].rsplit(" ", 1)[0] + " [...]"
    return USER_TEMPLATE.format(title=title or "", category=category or "", ...)
```
Dùng `.rsplit(" ", 1)[0]` để cắt tại ranh giới từ, không cắt giữa từ.

**6. `parse_label_json`:** parse JSON output robust:
- Thử `json.loads(raw)` trước.
- Nếu lỗi, thử `json.loads(raw, strict=False)` (cho phép newline trong string).
- Clamp `confidence > 1.0` → `1.0` (Gemini đôi khi trả 0.95*100 = 95).
- Nếu `summary is None` nhưng có `refusal_reason` → `summary = ""`.

### Bài tập 3.1 — render_user_prompt

**Yêu cầu:** Viết `render_user_prompt` cắt content ở ranh giới từ.

**Đáp án:**

```python
USER_TEMPLATE = """Tiêu đề: {title}
Chuyên mục: {category}
Nguồn: {source}

Nội dung:
\"\"\"
{content_text}
\"\"\"

Trả về JSON đúng schema:
{{"summary": "...", "key_entities": ["..."], "confidence": 0.0, "refusal_reason": null}}""".strip()

def render_user_prompt(*, title, category, source, content_text, content_max_chars=6000):
    snippet = content_text or ""
    if len(snippet) > content_max_chars:
        snippet = snippet[:content_max_chars].rsplit(" ", 1)[0] + " [...]"
    return USER_TEMPLATE.format(
        title=title or "", category=category or "", source=source, content_text=snippet,
    )
```

**Test:**
```python
long_text = "từ " * 3000  # 12000 ký tự
result = render_user_prompt(title="Test", category="thoi_su", source="vnexpress", content_text=long_text)
assert "[...]" in result
assert len(result) < 7000
```

### Bài tập 3.2 — parse_label_json

**Yêu cầu:** Viết `parse_label_json(raw_text)` trả `LabelOutput`. Xử lý:
1. JSON invalid → thử `strict=False` → raise `ValueError` nếu vẫn lỗi.
2. `confidence > 1.0` → clamp về `1.0`.
3. `summary is None` + có `refusal_reason` → `summary = ""`.

**Đáp án:**

```python
import json
from pydantic import BaseModel, Field, ValidationError

class LabelOutput(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    refusal_reason: str | None = None

def parse_label_json(raw_text: str) -> LabelOutput:
    try:
        data = json.loads(raw_text)
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
```

**Test:**
```python
# Bình thường
out = parse_label_json('{"summary":"Tin A.","key_entities":["VN"],"confidence":0.9,"refusal_reason":null}')
assert out.summary == "Tin A."

# Confidence > 1.0 → clamp
out = parse_label_json('{"summary":"X.","key_entities":[],"confidence":95.0}')
assert out.confidence == 1.0

# Refusal
out = parse_label_json('{"summary":null,"key_entities":[],"confidence":0.0,"refusal_reason":"not news"}')
assert out.summary == ""
assert out.refusal_reason == "not news"
```

### 🎯 Bài cuối chặng 3 — Code lại `labeling/prompt.py`

**Yêu cầu:** Tạo file `labeling/prompt.py` (105 dòng) chứa đầy đủ:
- `PROMPT_VERSION = "1.2.0"`, `PROMPT_MODEL = "gemini-2.5-flash"`, `PROMPT_PROVIDER = "aistudio"`
- `SYSTEM_PROMPT` — full text prompt biên tập viên
- `USER_TEMPLATE` — template có `{title}`, `{category}`, `{source}`, `{content_text}`
- `GenerationParams` dataclass (4 fields)
- `QcConfig` dataclass (5 fields: min_words=40, max_words=90, min_sentences=2, max_sentences=4, entity_fuzzy_min_ratio=0.85)
- `LabelOutput` BaseModel (4 fields)
- `render_user_prompt(...)` function
- `parse_label_json(raw_text)` function

**Kiểm tra:** So với `labeling/prompt.py` trong dự án — phải giống 100%.

---

## Chặng 4 — QC Rules (`labeling/qc.py`)

**Mục tiêu:** hiểu regex, Unicode normalization, fuzzy matching, entity extraction. Code lại `labeling/qc.py`.

### Lý thuyết

**1. Tại sao cần QC?**
LLM không hoàn hảo. Summary có thể quá ngắn, quá dài, bịa số liệu, bịa tên riêng. QC checks tự động loại bỏ nhãn xấu trước khi train model.

**2. Unicode NFC normalization:**
Tiếng Việt có 2 cách biểu diễn "ả": 1 ký tự (precomposed) hoặc 2 ký tự (base + combining mark). NFC đảm bảo thống nhất:
```python
import unicodedata
text = unicodedata.normalize("NFC", text)
```

**3. Regex cho tách câu:**
```python
import re
_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")
sentences = _SENT_SPLIT.split(text)
```
`\u2026` = "…" (ellipsis). `(?<=...)` = lookbehind — split sau dấu câu nhưng giữ lại dấu câu.

**4. Regex cho số và entity:**
```python
_NUMERIC = re.compile(r"\S*\d[\S]*")   # token chứa chữ số
_ENTITY = re.compile(r"(?:[A-ZĐ...][\wÀ-ỹ]*(?:\s+[A-ZĐ...][\wÀ-ỹ]*)+)")  # chuỗi từ viết hoa liên tiếp
```

**5. Fuzzy matching (rapidfuzz):**
```python
from rapidfuzz import fuzz
score = fuzz.partial_ratio("Nguyễn Văn A", "Ông Nguyễn Văn A cho biết...")
# score ≈ 100 vì "Nguyễn Văn A" nằm trong chuỗi dài hơn
```
Dự án dùng `partial_ratio >= 85%` để kiểm tra entity có trong source text không.

**6. Fallback khi không có rapidfuzz:**
```python
try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher
    class _FuzzFallback:
        @staticmethod
        def partial_ratio(a, b):
            return SequenceMatcher(None, a, b).ratio() * 100
    fuzz = _FuzzFallback()
```

**7. `_contains_numeric` logic:**
- Thử exact match trước.
- Collapse punctuation rồi thử lại.
- Cuối cùng tìm nhóm 3+ chữ số (`_DIGIT_GROUP`) trong source.

**8. `_contains_entity` logic:**
- Exact match → `True`.
- Collapse punct match → `True`.
- Fuzzy `partial_ratio >= min_ratio * 100` → `True`.
- Bất kỳ token nào >= 4 ký tự mà có trong source → `True`.

**9. `run_qc` flow:**
1. Normalize text (NFC).
2. Check refusal → add reason.
3. Word count check (40-90).
4. Sentence count check (2-4).
5. Number faithfulness (mọi số trong summary phải có trong source).
6. Entity faithfulness (mọi entity trong summary phải có trong source).
7. `passed = not reasons` (QC pass nếu không có reason nào).

### Bài tập 4.1 — Tách câu tiếng Việt

**Yêu cầu:** Viết `_sentences(text)` dùng regex.

**Đáp án:**

```python
import re
import unicodedata

_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")

def _norm(text):
    return unicodedata.normalize("NFC", text or "").strip()

def _sentences(text):
    return [part.strip() for part in _SENT_SPLIT.split(_norm(text)) if part.strip()]
```

**Test:**
```python
assert _sentences("Câu một. Câu hai! Câu ba?") == ["Câu một.", "Câu hai!", "Câu ba?"]
assert len(_sentences("Một câu duy nhất.")) == 1
```

### Bài tập 4.2 — Extract số và entity

**Yêu cầu:** Viết `_numerics(text)` và `_entities(text)`.

**Đáp án:**

```python
_NUMERIC = re.compile(r"\S*\d[\S]*")
_TITLE_CHARS = "A-ZĐÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ"
_ENTITY = re.compile(rf"(?:[{_TITLE_CHARS}][\wÀ-ỹ]*(?:\s+[{_TITLE_CHARS}][\wÀ-ỹ]*)+)")

def _numerics(text):
    out = []
    for match in _NUMERIC.finditer(text):
        token = match.group(0).strip(".,;:%()[]{}")
        if token:
            out.append(token)
    return out

def _entities(text):
    seen = set()
    out = []
    for match in _ENTITY.finditer(text):
        entity = match.group(0).strip()
        if entity and entity not in seen:
            seen.add(entity)
            out.append(entity)
    return out
```

**Test:**
```python
assert _numerics("Có 1.500 người và 30% tăng trưởng") == ["1.500", "30%"]
assert "Nguyễn Văn A" in _entities("Ông Nguyễn Văn A cho biết tại Hà Nội")
```

### Bài tập 4.3 — `_contains_numeric` và `_contains_entity`

**Yêu cầu:** Viết 2 function kiểm tra số/entity trong summary có xuất hiện trong source không.

**Đáp án:**

```python
_PUNCT_RE = re.compile(r"[\s\-\u2013\u2014\.\,;:\(\)\[\]\{\}/]+")
_DIGIT_GROUP = re.compile(r"\d{3,}")

def _collapse_punct(text):
    return _PUNCT_RE.sub(" ", text).strip()

def _contains_numeric(source, token):
    if token in source:
        return True
    collapsed_source = _collapse_punct(source)
    collapsed_token = _collapse_punct(token)
    if collapsed_token and collapsed_token in collapsed_source:
        return True
    groups = _DIGIT_GROUP.findall(token)
    return bool(groups and all(group in source for group in groups))

def _contains_entity(source, entity, *, min_ratio):
    if entity in source:
        return True
    collapsed_source = _collapse_punct(source)
    collapsed_entity = _collapse_punct(entity)
    if collapsed_entity and collapsed_entity in collapsed_source:
        return True
    if fuzz.partial_ratio(entity, source) >= min_ratio * 100:
        return True
    return any(len(token) >= 4 and token in source for token in entity.split())
```

### Bài tập 4.4 — `QcResult` và `run_qc`

**Yêu cầu:** Viết `QcResult` dataclass và `run_qc(output, source_text, cfg)`.

**Đáp án:**

```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class QcResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0
    missing_numbers: list[str] = field(default_factory=list)
    missing_entities: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "passed": self.passed, "reasons": self.reasons,
            "word_count": self.word_count, "sentence_count": self.sentence_count,
            "missing_numbers": self.missing_numbers, "missing_entities": self.missing_entities,
        }

def run_qc(*, output, source_text, cfg=None):
    cfg = cfg or QcConfig()
    summary = _norm(output.summary)
    source = _norm(source_text)
    reasons = []
    if output.refusal_reason:
        reasons.append(f"llm_refusal:{output.refusal_reason}")
    wc = _word_count(summary)
    if wc < cfg.min_words:
        reasons.append(f"too_short:{wc}<{cfg.min_words}")
    if wc > cfg.max_words:
        reasons.append(f"too_long:{wc}>{cfg.max_words}")
    sc = len(_sentences(summary))
    if sc < cfg.min_sentences:
        reasons.append(f"too_few_sentences:{sc}<{cfg.min_sentences}")
    if sc > cfg.max_sentences:
        reasons.append(f"too_many_sentences:{sc}>{cfg.max_sentences}")
    missing_numbers = [t for t in _numerics(summary) if not _contains_numeric(source, t)]
    if missing_numbers:
        reasons.append(f"unsupported_numbers:{','.join(missing_numbers[:5])}")
    missing_entities = [
        e for e in _entities(summary)
        if not _contains_entity(source, e, min_ratio=cfg.entity_fuzzy_min_ratio)
    ]
    if missing_entities:
        reasons.append(f"unsupported_entities:{','.join(missing_entities[:5])}")
    return QcResult(
        passed=not reasons, reasons=reasons, word_count=wc, sentence_count=sc,
        missing_numbers=missing_numbers, missing_entities=missing_entities,
    )
```

### 🎯 Bài cuối chặng 4 — Code lại `labeling/qc.py`

**Yêu cầu:** Tạo file `labeling/qc.py` (153 dòng) chứa đầy đủ:
- Import `rapidfuzz` với fallback `difflib`
- 6 regex constants: `_SENT_SPLIT`, `_NUMERIC`, `_PUNCT_RE`, `_DIGIT_GROUP`, `_TITLE_CHARS`, `_ENTITY`
- Helper functions: `_norm`, `_word_count`, `_sentences`, `_numerics`, `_collapse_punct`, `_contains_numeric`, `_entities`, `_contains_entity`
- `QcResult` dataclass (6 fields + `to_dict`)
- `run_qc(output, source_text, cfg)` function

**Kiểm tra:** So với `labeling/qc.py` trong dự án — phải giống 100%.

---

## Chặng 5 — AI Studio Labeler (`labeling/gemini_labeler.py`)

**Mục tiêu:** hiểu google.genai SDK, key rotation, model fallback, retry, thread safety. Code lại `labeling/gemini_labeler.py`.

### Lý thuyết

**1. Google AI Studio:**
- Miễn phí, dùng API key (chuỗi ký tự), giới hạn request/phút.
- Lấy key tại https://aistudio.google.com/apikey

**2. SDK `google-genai`:**
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_KEY")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Xin chào",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=4096,
        response_mime_type="application/json",
    ),
)
print(response.text)
```

**3. Key rotation (per-call local iteration):**
Khi nhiều thread cùng gọi API (qua `asyncio.to_thread`), nếu dùng shared state để xoay key → race condition. Giải pháp: mỗi lần gọi `generate()`, copy danh sách key ra biến local rồi iterate qua từng key.

```python
def generate(self, *, system, user):
    keys = list(self._keys)        # local copy, thread-safe
    models = list(self._model_chain)
    for model_name in models:
        for key_idx, api_key in enumerate(keys):
            try:
                # gọi API với key này
                ...
                return text
            except QuotaError:
                continue  # thử key tiếp
        # Hết key cho model này → thử model tiếp
    raise GeminiLLMError("All models/keys exhausted")
```

**4. Model fallback chain:**
`["gemini-2.5-flash", "gemini-2.0-flash"]` — nếu model đầu không khả dụng ("not found"), tự chuyển sang model tiếp.

**5. Error classification:**
- **Quota/rate limit** (429, "resource exhausted") → thử key tiếp.
- **Transient** (500, 503, timeout) → raise `GeminiTransientError` → tenacity retry.
- **Model not found** → break, thử model tiếp.
- **Other** → raise `GeminiLLMError` (unrecoverable).

**6. Retry với tenacity:**
```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

@retry(
    reraise=True,
    retry=retry_if_exception_type(GeminiTransientError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(6),
)
def generate(self, ...):
    ...
```
Chỉ retry `GeminiTransientError`. Nếu `GeminiLLMError` → dừng ngay.

**7. `except GeminiLLMError: raise` trước `except Exception`:**
Khi `response.text is None`, raise `GeminiLLMError` bên trong `try`. Nếu không có `except GeminiLLMError: raise`, exception bị catch bởi `except Exception` → xử lý sai.

**8. Thread-safe client cache:**
```python
self._clients_lock = threading.Lock()

def _get_client(self, api_key):
    with self._clients_lock:
        if api_key not in self._clients:
            self._clients[api_key] = genai.Client(api_key=api_key)
        return self._clients[api_key]
```

### Bài tập 5.1 — Đọc key từ environment

**Yêu cầu:** Viết `_keys_from_env()` giống dự án.

**Đáp án:**

```python
import os

class GeminiLLMError(RuntimeError):
    pass

def _keys_from_env():
    raw = os.environ.get("GEMINI_API_KEYS", "").strip()
    if not raw:
        single = os.environ.get("GEMINI_API_KEY", "").strip()
        if single:
            return [single]
        raise GeminiLLMError("Set GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY")
    return [k.strip() for k in raw.split(",") if k.strip()]
```

### Bài tập 5.2 — Per-call key iteration (không có API thật)

**Yêu cầu:** Viết function `try_all_keys(keys, model, call_fn)` iterate qua keys, nếu `QuotaError` → thử key tiếp.

**Đáp án:**

```python
class QuotaError(Exception):
    pass

def try_all_keys(keys, model, call_fn):
    last_exc = None
    for key_idx, key in enumerate(keys):
        try:
            return call_fn(key, model)
        except QuotaError as exc:
            last_exc = exc
            continue
    raise RuntimeError(f"All {len(keys)} keys exhausted. Last: {last_exc}")
```

**Test:**

```python
call_count = 0
def fake_call(key, model):
    global call_count
    call_count += 1
    if key in ("k1", "k2"):
        raise QuotaError(f"{key} exhausted")
    return f"OK with {key}"

result = try_all_keys(["k1", "k2", "k3"], "gemini-2.5-flash", fake_call)
assert result == "OK with k3"
assert call_count == 3
```

### Bài tập 5.3 — Error classification

**Yêu cầu:** Viết function `classify_error(exc)` trả `"quota"`, `"transient"`, `"model_not_found"`, hoặc `"fatal"`.

**Đáp án:**

```python
def classify_error(exc):
    err = str(exc).lower()
    if any(m in err for m in ("429", "resource has been exhausted", "quota", "rate limit", "too many requests")):
        return "quota"
    if any(m in err for m in ("deadline", "unavailable", "internal", "timeout", "503", "500")):
        return "transient"
    if "not found" in err or "does not exist" in err or "invalid" in err:
        return "model_not_found"
    return "fatal"
```

### 🎯 Bài cuối chặng 5 — Code lại `labeling/gemini_labeler.py`

**Yêu cầu:** Tạo file `labeling/gemini_labeler.py` (182 dòng) chứa đầy đủ:
- Module docstring
- `DEFAULT_MODEL_CHAIN = ["gemini-2.5-flash", "gemini-2.0-flash"]`
- `GeminiLLMError`, `GeminiTransientError` exception classes
- `OverrideFn` type alias
- `GeminiLabeler` class:
  - `__init__` (api_keys, model_chain, params, override_callable)
  - `_get_client` (thread-safe with Lock)
  - `generate` (tenacity retry, per-call local iteration, error classification, `except GeminiLLMError: raise`)
- `_keys_from_env()` function

**Kiểm tra:** So với `labeling/gemini_labeler.py` trong dự án — phải giống 100%.

---

## Chặng 6 — Label Dataset Pipeline (`labeling/label_dataset.py`)

**Mục tiêu:** hiểu asyncio.to_thread, semaphore, pipeline orchestration. Code lại `labeling/label_dataset.py`.

### Lý thuyết

**1. `asyncio.to_thread`:**
`GeminiLabeler.generate()` là sync function (blocking I/O). Để gọi nó trong async context:
```python
raw = await asyncio.to_thread(labeler.generate, system=SYSTEM_PROMPT, user=user_prompt)
```
Python chạy `generate()` trong thread pool, không block event loop.

**2. `asyncio.Semaphore`:**
Giới hạn concurrent requests. `Semaphore(5)` = tối đa 5 request cùng lúc:
```python
semaphore = asyncio.Semaphore(5)
async with semaphore:
    result = await asyncio.to_thread(...)
```

**3. `asyncio.gather`:**
Chạy nhiều coroutine đồng thời:
```python
tasks = [_label_one(row, labeler=labeler, semaphore=sem) for row in rows]
results = await asyncio.gather(*tasks)
```

**4. Pipeline flow:**
```
read_jsonl → rows → label_rows → [_label_one(row) for each row] → write_jsonl
                                      ↓
                               render_user_prompt
                               labeler.generate
                               parse_label_json
                               run_qc
                               → labeled dict with summary, entities, qc_passed
```

**5. Error handling:**
`_label_one` catch `GeminiLLMError`, `GeminiTransientError`, `ValueError` → trả row với `summary=""`, `qc_passed=False` thay vì crash toàn pipeline.

### Bài tập 6.1 — asyncio.to_thread + Semaphore

**Yêu cầu:** Viết async function gọi sync `fake_generate(text)` qua `to_thread` với semaphore=2.

**Đáp án:**

```python
import asyncio, time

def fake_generate(text):
    time.sleep(0.1)  # giả lập API call
    return f"Summary of: {text[:20]}"

async def label_batch(texts, concurrency=2):
    sem = asyncio.Semaphore(concurrency)
    async def label_one(text):
        async with sem:
            return await asyncio.to_thread(fake_generate, text)
    return await asyncio.gather(*[label_one(t) for t in texts])

results = asyncio.run(label_batch(["Bài 1 nội dung dài...", "Bài 2 nội dung dài...", "Bài 3..."]))
assert len(results) == 3
```

### Bài tập 6.2 — _label_one với error handling

**Yêu cầu:** Viết `_label_one(row, labeler, semaphore)` trả dict đầy đủ fields. Nếu lỗi → trả dict với `summary=""`, `qc_passed=False`.

**Đáp án:**

```python
async def _label_one(row, *, labeler, semaphore):
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
        qc = run_qc(output=output, source_text=f"{row.get('title') or ''} {row.get('content_text') or ''}")
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
            "summary": "", "key_entities": [], "confidence": 0.0,
            "refusal_reason": str(exc), "prompt_version": PROMPT_VERSION,
            "qc_passed": False,
            "qc_details": {"passed": False, "reasons": [f"label_error:{exc}"]},
        }
```

### 🎯 Bài cuối chặng 6 — Code lại `labeling/label_dataset.py`

**Yêu cầu:** Tạo file `labeling/label_dataset.py` (133 dòng) chứa đầy đủ:
- `read_jsonl`, `write_jsonl` functions
- `_label_one(row, labeler, semaphore)` async function
- `label_rows(rows, concurrency, limit, labeler)` async function
- `_build_parser()` → argparse (--input, --output, --limit, --concurrency)
- `_run_cli(args)` async function
- `main(argv)` function

**Kiểm tra:** So với `labeling/label_dataset.py` trong dự án — phải giống 100%.

---

## Chặng 7 — Split Dataset (`labeling/split_dataset.py`)

**Mục tiêu:** hiểu hash-based deterministic split, JSONL export. Code lại `labeling/split_dataset.py`.

### Lý thuyết

**1. Deterministic split bằng hash:**
Thay vì random split (kết quả khác nhau mỗi lần), dùng SHA-256 hash của `article_id`:
```python
import hashlib

def split_bucket(article_id, *, salt="vn-news-v1"):
    digest = hashlib.sha256(f"{salt}:{article_id}".encode()).digest()
    bucket = digest[0]  # byte đầu tiên: 0-255
    if bucket < 26:     # ~10%
        return "test"
    if bucket < 52:     # ~10%
        return "val"
    return "train"      # ~80%
```
Cùng `article_id` luôn vào cùng split. Không cần lưu trạng thái.

**2. `dataset_record`:** chọn fields cần thiết cho training:
```python
def dataset_record(row):
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
```

**3. Filter:** chỉ lấy rows có `qc_passed=True` và có `content_text` + `summary`.

**4. `--check-v2-counts`:** flag kiểm tra số lượng khớp với report lịch sử.

### Bài tập 7.1 — split_bucket

**Yêu cầu:** Viết `split_bucket(article_id)` và test tính deterministic.

**Đáp án:**

```python
import hashlib
from typing import Literal

SplitName = Literal["train", "val", "test"]

def split_bucket(article_id: int, *, salt: str = "vn-news-v1") -> SplitName:
    digest = hashlib.sha256(f"{salt}:{article_id}".encode()).digest()
    bucket = digest[0]
    if bucket < 26:
        return "test"
    if bucket < 52:
        return "val"
    return "train"
```

**Test:**
```python
# Deterministic: chạy 2 lần cho kết quả giống nhau
assert split_bucket(1) == split_bucket(1)
assert split_bucket(100) == split_bucket(100)
# Phân bố: đa số vào train
from collections import Counter
dist = Counter(split_bucket(i) for i in range(1000))
assert dist["train"] > dist["val"]
assert dist["train"] > dist["test"]
```

### 🎯 Bài cuối chặng 7 — Code lại `labeling/split_dataset.py`

**Yêu cầu:** Tạo file `labeling/split_dataset.py` (100 dòng) chứa đầy đủ:
- `SplitName` type alias
- `EXPECTED_V2_COUNTS = {"train": 1636, "val": 218, "test": 216}`
- `split_bucket(article_id, salt)` function
- `read_jsonl`, `write_jsonl` functions
- `dataset_record(row)` function
- `split_rows(rows)` function — filter `qc_passed`, split by hash
- `export_splits(input_path, output_dir)` function
- `_build_parser()` → argparse
- `main(argv)` function

**Kiểm tra:** So với `labeling/split_dataset.py` trong dự án — phải giống 100%.

---

## Chặng 8 — Crawler phần 1: URL, Text, Robots (`app/crawler.py` dòng 1-250)

**Mục tiêu:** hiểu URL canonicalization, SimHash, text normalization, robots.txt, polite HTTP client. Code lại nửa đầu `app/crawler.py`.

### Lý thuyết

**1. URL canonicalization:**
Cùng một bài báo có nhiều URL variant:
- `https://vnexpress.net/bai-viet-123.html?utm_source=fb`
- `http://vnexpress.net/bai-viet-123.html`
- `https://VNEXPRESS.NET//bai-viet-123.html/`

`canonicalize_url` chuẩn hóa tất cả về 1 URL:
```python
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", ...)

def canonicalize_url(url):
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    # Bỏ port mặc định
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]
    # Bỏ tracking params
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
             if not any(k.lower().startswith(p) for p in _TRACKING_PREFIXES)]
    pairs.sort()
    path = parts.path or "/"
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((scheme, netloc, path, urlencode(pairs, doseq=True), ""))
```

**2. URL hash:** `SHA-256(canonical_url)[:32]` → unique ID.

**3. SimHash (near-duplicate detection):**
- Mỗi bài báo → character n-grams → weighted features → 64-bit hash.
- 2 bài gần giống nhau → Hamming distance <= 3.
```python
from simhash import Simhash
from collections import Counter

def _simhash_features(text):
    joined = "".join(re.findall(r"[\w\u4e00-\u9fcc]+", text.lower()))
    if len(joined) < 4:
        return {joined: 1} if joined else {}
    counts = Counter(joined[i:i+4] for i in range(len(joined) - 3))
    return {f: min(w, 50) for f, w in counts.items()}

def simhash64(text):
    features = _simhash_features(text)
    if not features:
        return 0
    value = int(Simhash(features, f=64).value) & ((1 << 64) - 1)
    if value >= (1 << 63):
        value -= 1 << 64
    return value

def hamming(a, b):
    return bin((a ^ b) & ((1 << 64) - 1)).count("1")
```

**4. Text normalization:**
```python
import unicodedata, re

_WS_RE = re.compile(r"\s+")
_BOILERPLATE_RE = re.compile(
    r"(?im)^\s*(?:đọc thêm|xem thêm|tags?:|từ khóa:|liên quan:|chia sẻ).*$"
)

def normalize_text(text):
    text = unicodedata.normalize("NFC", text or "")
    text = _BOILERPLATE_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()
```

**5. robots.txt:**
```python
from urllib.robotparser import RobotFileParser

parser = RobotFileParser("https://vnexpress.net/robots.txt")
parser.parse(robots_text.splitlines())
can_fetch = parser.can_fetch("vn-news-summarizer-research/0.1", url)
```

**6. PoliteClient (async HTTP với rate limiting):**
- Per-host asyncio Lock → chỉ 1 request tại một thời điểm per host.
- `crawl_delay_s` giữa các request.
- Retry với tenacity: 429, 5xx → retry.

**7. RobotsCache:**
Cache `RobotFileParser` per host, chỉ fetch `robots.txt` 1 lần.

### Bài tập 8.1 — canonicalize_url

**Yêu cầu:** Viết `canonicalize_url(url)`.

**Test:**
```python
assert canonicalize_url("https://vnexpress.net/bai.html?utm_source=fb") == "https://vnexpress.net/bai.html"
assert canonicalize_url("HTTP://VNEXPRESS.NET:80//bai.html/") == "http://vnexpress.net/bai.html"
assert canonicalize_url("https://a.com/b?z=1&a=2") == "https://a.com/b?a=2&z=1"
```

### Bài tập 8.2 — SimHash + Hamming

**Yêu cầu:** Viết `simhash64(text)` và `hamming(a, b)`.

**Test:**
```python
h1 = simhash64("Hà Nội hôm nay trời nắng đẹp, nhiệt độ 32 độ C")
h2 = simhash64("Hà Nội hôm nay trời nắng đẹp, nhiệt độ 33 độ C")  # gần giống
h3 = simhash64("Bóng đá Việt Nam thắng Thái Lan 2-0 tại SEA Games")  # khác hẳn
assert hamming(h1, h2) <= 5    # gần giống → Hamming nhỏ
assert hamming(h1, h3) > 10    # khác hẳn → Hamming lớn
```

### Bài tập 8.3 — normalize_text

**Yêu cầu:** Viết `normalize_text(text)` loại bỏ boilerplate, gộp whitespace, NFC.

**Test:**
```python
assert normalize_text("  Tin  tức   hôm nay  ") == "Tin tức hôm nay"
assert normalize_text("Nội dung.\nĐọc thêm: bài liên quan") == "Nội dung."
```

### Bài tập 8.4 — PoliteClient

**Yêu cầu:** Viết `PoliteClient` class với per-host lock, crawl delay, retry.

**Đáp án (rút gọn):**

```python
import asyncio, time, random
import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential
from urllib.parse import urlsplit

class PoliteClient:
    def __init__(self, *, user_agent, timeout_s=20.0, crawl_delay_s=1.0, max_retries=3):
        self._client = httpx.AsyncClient(
            timeout=timeout_s,
            headers={"User-Agent": user_agent, "Accept-Language": "vi,en;q=0.7"},
            follow_redirects=True,
        )
        self._min_interval = max(crawl_delay_s, 0.0)
        self._last_by_host = {}
        self._locks = {}
        self._max_retries = max_retries

    async def get(self, url):
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
            retry=retry_if_exception_type(httpx.HTTPError), reraise=True,
        ):
            with attempt:
                response = await self._client.get(url)
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"retryable status {response.status_code}",
                        request=response.request, response=response,
                    )
                return response
        raise RuntimeError("unreachable")

    async def aclose(self):
        await self._client.aclose()
```

### 🎯 Bài cuối chặng 8 — Code lại `app/crawler.py` dòng 1-250

**Yêu cầu:** Code lại phần đầu `app/crawler.py` (khoảng 250 dòng) gồm:
- Tất cả imports
- Constants: `_WS_RE`, `_BOILERPLATE_RE`, `_CATEGORY_FROM_PATH_RE`, `_SIMHASH_TOKEN_RE`, `_SIMHASH_NGRAM_WIDTH`, `_SIMHASH_WEIGHT_CAP`, `_TRACKING_PREFIXES`
- `ExtractedArticle` dataclass
- `PoliteClient` class (full)
- `RobotsCache` class (full)
- Functions: `normalize_text`, `word_count`, `canonicalize_url`, `url_hash`, `_simhash_features`, `simhash64`, `hamming`, `_to_utc`, `_category_from_url`

**Kiểm tra:** So với `app/crawler.py` dòng 1-257 trong dự án.

---

## Chặng 9 — Crawler phần 2: Feed, Extract, Orchestration (`app/crawler.py` dòng 250-514)

**Mục tiêu:** hiểu RSS parsing, HTML extraction, crawler orchestration. Code lại nửa sau `app/crawler.py`.

### Lý thuyết

**1. RSS parsing với feedparser:**
```python
import feedparser
parsed = feedparser.parse(response.content)
for entry in parsed.entries:
    link = entry.get("link")
    title = entry.get("title")
    category = entry.get("tags", [{}])[0].get("term") if entry.get("tags") else None
    published = entry.get("published") or entry.get("updated")
```

**2. HTML extraction — trafilatura + readability fallback:**
```python
import trafilatura, json
from readability import Document
from bs4 import BeautifulSoup

# Thử trafilatura trước (chính xác hơn)
extracted = trafilatura.extract(html, url=url, with_metadata=True, output_format="json",
                                include_comments=False, include_tables=False, favor_precision=True)
if extracted:
    doc = json.loads(extracted)
    text = doc.get("text")

# Fallback: readability + BeautifulSoup
if text is None:
    doc = Document(html)
    soup = BeautifulSoup(doc.summary(), "lxml")
    text = soup.get_text(" ")
```

**3. Date parsing:**
```python
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def _to_utc(raw):
    if isinstance(raw, datetime):
        dt = raw
    else:
        dt = parsedate_to_datetime(str(raw))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
```

**4. `crawl_articles` orchestration:**
```
for source in enabled_sources:
    for feed_url in source.rss:
        candidates = fetch_feed(feed_url)
    for candidate in candidates:
        if URL đã thấy → skip (dedupe)
        if robots.txt cấm → skip
        response = client.get(url)
        extracted = extract_from_html(response.text)
        if extracted is None → skip
        if SimHash gần giống bài đã crawl → skip (near-dedupe)
        → CrawledArticle → articles list
```

**5. CLI:**
- `--mode {labeling, demo}` — demo mặc định 5 bài, labeling không giới hạn.
- `--output` — ghi JSONL.
- `--source` — chỉ crawl nguồn cụ thể.
- `--verbose` — in progress.

### Bài tập 9.1 — fetch_feed

**Yêu cầu:** Viết `fetch_feed(client, source, feed_url)` trả `list[ArticleCandidate]`.

**Đáp án:**

```python
async def fetch_feed(client, *, source, feed_url):
    try:
        response = await client.get(feed_url)
    except Exception as exc:
        print(f"[crawler] RSS fetch failed {feed_url}: {exc}", file=sys.stderr)
        return []
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        return []
    candidates = []
    for entry in parsed.entries:
        link = str(entry.get("link") or "")
        title = str(entry.get("title") or "").strip()
        if not link or not title:
            continue
        category = None
        if entry.get("tags"):
            category = entry["tags"][0].get("term") or None
        candidates.append(ArticleCandidate(
            source=source.id, source_name=source.name,
            url=canonicalize_url(link), title=normalize_text(title),
            published_at=_to_utc(entry.get("published") or entry.get("updated") or entry.get("pubDate") or entry.get("dc_date")),
            category=canonical_category(category or _category_from_url(link)),
            author=(str(entry.get("author")) if entry.get("author") else None),
        ))
    return candidates
```

### Bài tập 9.2 — extract_from_html

**Yêu cầu:** Viết `extract_from_html(html, url)` → `ExtractedArticle | None`.

**Đáp án:**

```python
def extract_from_html(html, *, url=None):
    if not html:
        return None
    try:
        extracted = trafilatura.extract(html, url=url, with_metadata=True, output_format="json",
                                        include_comments=False, include_tables=False, favor_precision=True)
        if extracted:
            doc = json.loads(extracted)
            text = normalize_text(str(doc.get("text") or ""))
            if word_count(text) >= 50:
                return ExtractedArticle(
                    title=(str(doc.get("title")) if doc.get("title") else None),
                    author=(str(doc.get("author")) if doc.get("author") else None),
                    published_at=_to_utc(doc.get("date")),
                    language=(str(doc.get("language")) if doc.get("language") else None),
                    content_text=text, word_count=word_count(text),
                )
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    try:
        doc = Document(html)
        soup = BeautifulSoup(doc.summary(), "lxml")
        text = normalize_text(soup.get_text(" "))
        if word_count(text) >= 50:
            return ExtractedArticle(
                title=doc.short_title() or None, author=None,
                published_at=None, language=None,
                content_text=text, word_count=word_count(text),
            )
    except Exception:
        pass
    return None
```

### 🎯 Bài cuối chặng 9 — Code lại `app/crawler.py` hoàn chỉnh

**Yêu cầu:** Tạo file `app/crawler.py` (514 dòng) đầy đủ, kết hợp chặng 8 + chặng 9:
- Tất cả imports, constants, classes từ chặng 8
- `fetch_feed`, `extract_from_html` từ chặng 9
- `crawl_articles` async function (full orchestration logic)
- `write_jsonl`, `_validate_cli_output_path`, `_build_parser`, `_run_cli`, `main`

**Kiểm tra:** So với `app/crawler.py` trong dự án — phải giống 100%.

---

## Chặng 10 — ViT5 Summarizer (`app/summarizer.py`)

**Mục tiêu:** hiểu lazy loading, PEFT adapter, tokenizer, batch inference. Code lại `app/summarizer.py`.

### Lý thuyết

**1. Lazy loading:**
Model nặng (hàng GB). Không load ngay khi tạo object, mà load lần đầu gọi `summarize()`:
```python
class ViT5Summarizer:
    def __init__(self, model_id=None, ...):
        self.model_id = model_id or os.environ.get("HF_MODEL_ID") or "VietAI/vit5-base"
        self._model = None  # chưa load
        self._tokenizer = None

    def _ensure_loaded(self):
        if self._model is not None:
            return self._model, self._tokenizer
        # Load model + tokenizer ở đây
        ...
```

**2. PEFT adapter loading:**
Model fine-tune bằng LoRA chỉ lưu adapter nhỏ (~vài MB), không lưu full model. Load:
```python
from peft import PeftConfig, PeftModel

peft_cfg = PeftConfig.from_pretrained(adapter_id)
base_model = AutoModelForSeq2SeqLM.from_pretrained(peft_cfg.base_model_name_or_path)
model = PeftModel.from_pretrained(base_model, adapter_id)
```

Nếu `model_id` không phải PEFT adapter → load trực tiếp:
```python
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
```

**3. `GenerationConfig`:**
```python
@dataclass(slots=True)
class GenerationConfig:
    max_input_length: int = 1024    # cắt input dài hơn 1024 token
    max_new_tokens: int = 128       # summary tối đa 128 token
    num_beams: int = 4              # beam search cho chất lượng
    no_repeat_ngram_size: int = 3   # không lặp 3-gram
    length_penalty: float = 1.0
    early_stopping: bool = True
    batch_size: int = 4
```

**4. Batch inference:**
```python
def summarize_batch(self, texts):
    # Filter empty texts
    empty_mask = [not text or not text.strip() for text in texts]
    non_empty = [t for t, empty in zip(texts, empty_mask) if not empty]
    # Tokenize + generate in batches
    for start in range(0, len(non_empty), self.generation.batch_size):
        batch = non_empty[start:start + batch_size]
        inputs = tokenizer(batch, max_length=1024, truncation=True, padding=True, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=128, num_beams=4, ...)
        decoded.extend(tokenizer.batch_decode(outputs, skip_special_tokens=True))
    # Re-insert empty strings
    ...
```

**5. Tokenizer source cho PEFT:**
PEFT adapter thường không chứa tokenizer. Nếu local path không có `tokenizer.json`, dùng tokenizer từ base model:
```python
tokenizer_source = self.model_id
if Path(self.model_id).exists() and not (Path(self.model_id) / "tokenizer.json").exists():
    tokenizer_source = base_name
```

### Bài tập 10.1 — GenerationConfig

**Yêu cầu:** Tạo `GenerationConfig` dataclass.

**Đáp án:**

```python
from dataclasses import dataclass

@dataclass(slots=True)
class GenerationConfig:
    max_input_length: int = 1024
    max_new_tokens: int = 128
    num_beams: int = 4
    no_repeat_ngram_size: int = 3
    length_penalty: float = 1.0
    early_stopping: bool = True
    batch_size: int = 4
```

### Bài tập 10.2 — Lazy loading pattern

**Yêu cầu:** Viết `_ensure_loaded` với PEFT fallback logic.

**Đáp án:**

```python
def _load_as_peft_adapter(self, transformers):
    try:
        from peft import PeftConfig, PeftModel
        peft_cfg = PeftConfig.from_pretrained(self.model_id, token=self.token)
        base_name = self.base_model_id or peft_cfg.base_model_name_or_path
        base_model = transformers.AutoModelForSeq2SeqLM.from_pretrained(base_name, token=self.token)
        model = PeftModel.from_pretrained(base_model, self.model_id, token=self.token)
        tokenizer_source = self.model_id
        if Path(self.model_id).exists() and not (Path(self.model_id) / "tokenizer.json").exists():
            tokenizer_source = base_name
        tokenizer = transformers.AutoTokenizer.from_pretrained(tokenizer_source, token=self.token)
        return model, tokenizer
    except Exception:
        return None

def _ensure_loaded(self):
    if self._model is not None and self._tokenizer is not None:
        return self._model, self._tokenizer
    import transformers
    loaded = self._load_as_peft_adapter(transformers)
    if loaded is None:
        model = transformers.AutoModelForSeq2SeqLM.from_pretrained(self.model_id, token=self.token)
        tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_id, token=self.token)
    else:
        model, tokenizer = loaded
    if self.device:
        model.to(self.device)
    model.eval()
    self._model = model
    self._tokenizer = tokenizer
    return model, tokenizer
```

### Bài tập 10.3 — summarize_batch

**Yêu cầu:** Viết `summarize_batch(texts)` xử lý empty texts, batch processing, re-insert empty.

**Đáp án:**

```python
def summarize_batch(self, texts):
    if not texts:
        return []
    empty_mask = [not text or not text.strip() for text in texts]
    non_empty = [text for text, is_empty in zip(texts, empty_mask, strict=True) if not is_empty]
    if not non_empty:
        return ["" for _ in texts]
    model, tokenizer = self._ensure_loaded()
    decoded = []
    for start in range(0, len(non_empty), self.generation.batch_size):
        batch = non_empty[start:start + self.generation.batch_size]
        inputs = tokenizer(batch, max_length=self.generation.max_input_length,
                          truncation=True, padding=True, return_tensors="pt")
        if self.device:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = model.generate(
            **inputs, max_new_tokens=self.generation.max_new_tokens,
            num_beams=self.generation.num_beams,
            no_repeat_ngram_size=self.generation.no_repeat_ngram_size,
            length_penalty=self.generation.length_penalty,
            early_stopping=self.generation.early_stopping,
        )
        decoded.extend(str(x) for x in tokenizer.batch_decode(outputs, skip_special_tokens=True))
    result = []
    cursor = 0
    for is_empty in empty_mask:
        if is_empty:
            result.append("")
        else:
            result.append(decoded[cursor])
            cursor += 1
    return result
```

### 🎯 Bài cuối chặng 10 — Code lại `app/summarizer.py`

**Yêu cầu:** Tạo file `app/summarizer.py` (138 dòng) chứa đầy đủ:
- `GenerationConfig` dataclass (7 fields)
- `ViT5Summarizer` class:
  - `__init__` (model_id, base_model_id, token, device, generation)
  - `_load_as_peft_adapter(transformers)` → `tuple | None`
  - `_ensure_loaded()` → `(model, tokenizer)`
  - `summarize(text)` → str
  - `summarize_batch(texts)` → list[str]

**Kiểm tra:** So với `app/summarizer.py` trong dự án — phải giống 100%.

---

## Chặng 11 — FastAPI Web Demo (`app/main.py` + `app/templates/index.html`)

**Mục tiêu:** hiểu FastAPI routes, Jinja2 templates, fetch API, XSS prevention. Code lại `app/main.py` và `index.html`.

### Lý thuyết

**1. FastAPI app:**
```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="vn-news-summarizer", version="0.2.0-simple")
templates = Jinja2Templates(directory="app/templates")
summarizer = ViT5Summarizer()  # global, lazy loaded
```

**2. Routes:**
- `GET /` → render `index.html` template
- `GET /healthz` → `{"status": "ok", "version": "..."}`
- `POST /api/summarize-today` → crawl RSS → summarize → JSON response

**3. Jinja2 template variables:**
```python
templates.TemplateResponse("index.html", {
    "request": request,  # bắt buộc
    "model_id": summarizer.model_id,
    "max_articles": int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5")),
})
```
Trong HTML: `{{ model_id }}`, `{{ max_articles }}`.

**4. POST endpoint logic:**
```python
@app.post("/api/summarize-today", response_model=SummarizeResponse)
async def summarize_today():
    articles, _stats = await crawl_articles(mode="demo", limit=limit)
    if not articles:
        raise HTTPException(status_code=502, detail="No article could be crawled")
    summaries = summarizer.summarize_batch([a.content_text for a in articles])
    items = [SummaryItem(...) for a, s in zip(articles, summaries)]
    return SummarizeResponse(date=date.today().isoformat(), total=len(items), items=items)
```

**5. XSS prevention trong `index.html`:**
```javascript
function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
```
Mọi dữ liệu từ server (title, summary, URL) phải qua `escapeHtml()` trước khi chèn vào DOM.

**6. Frontend fetch:**
```javascript
const response = await fetch("/api/summarize-today", { method: "POST" });
const data = await response.json();
if (!response.ok) throw new Error(data.detail || "Request failed");
```

### Bài tập 11.1 — FastAPI routes

**Yêu cầu:** Viết 3 routes: `GET /`, `GET /healthz`, `POST /api/summarize-today`.

**Đáp án:**

```python
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
app = FastAPI(title="vn-news-summarizer", version=APP_VERSION,
              description="Vietnamese news summarization demo using RSS crawl + fine-tuned ViT5.")
templates = Jinja2Templates(directory="app/templates")
summarizer = ViT5Summarizer()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "model_id": summarizer.model_id,
        "max_articles": int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5")),
    })

@app.get("/healthz", response_model=HealthResponse)
async def healthz():
    return HealthResponse(status="ok", version=APP_VERSION)

@app.post("/api/summarize-today", response_model=SummarizeResponse)
async def summarize_today():
    limit = int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5"))
    articles, _stats = await crawl_articles(mode="demo", limit=limit)
    if not articles:
        raise HTTPException(status_code=502, detail="No article could be crawled and extracted.")
    try:
        summaries = summarizer.summarize_batch([a.content_text for a in articles])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {exc}") from exc
    items = [
        SummaryItem(title=a.title, source=a.source_name, url=a.url,
                    published_at=a.published_at, summary=s)
        for a, s in zip(articles, summaries, strict=True)
    ]
    return SummarizeResponse(date=date.today().isoformat(), total=len(items), items=items)
```

### Bài tập 11.2 — escapeHtml + fetch

**Yêu cầu:** Viết JavaScript cho nút "Tóm tắt tin tức hôm nay" với XSS escaping.

**Đáp án:**

```javascript
function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

button.addEventListener("click", async () => {
    button.disabled = true;
    statusEl.textContent = "Đang crawl và tóm tắt...";
    resultsEl.innerHTML = "";
    try {
        const response = await fetch("/api/summarize-today", { method: "POST" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Request failed");
        statusEl.textContent = `Đã tóm tắt ${data.total} bài ngày ${data.date}.`;
        resultsEl.innerHTML = data.items.map((item) => `
            <article class="item">
                <h2>${escapeHtml(item.title)}</h2>
                <p class="meta">${escapeHtml(item.source)}${item.published_at ? " - " + escapeHtml(item.published_at) : ""}</p>
                <p>${escapeHtml(item.summary)}</p>
                <p class="meta">Tóm tắt bởi mô hình AI, có thể chưa chính xác.</p>
                <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer nofollow">Đọc bài gốc</a>
            </article>
        `).join("");
    } catch (error) {
        statusEl.textContent = `Lỗi: ${error.message}`;
    } finally {
        button.disabled = false;
    }
});
```

### 🎯 Bài cuối chặng 11 — Code lại `app/main.py` + `app/templates/index.html`

**Yêu cầu:**
1. Tạo `app/main.py` (66 dòng): 3 routes, global summarizer, APP_VERSION.
2. Tạo `app/templates/index.html` (140 dòng): HTML + CSS + JavaScript với:
   - CSS variables (--bg, --panel, --text, --muted, --line, --accent, --accent-dark)
   - Responsive layout (`@media max-width 720px`)
   - Nút "Tóm tắt tin tức hôm nay"
   - `escapeHtml` function
   - `fetch("/api/summarize-today")` + render results
   - Jinja2 placeholders: `{{ model_id }}`, `{{ max_articles }}`

**Kiểm tra:** So với `app/main.py` và `app/templates/index.html` trong dự án — phải giống 100%.

---

## Tổng Kết — Thứ Tự Code Lại Dự Án Hoàn Chỉnh

Sau khi hoàn thành tất cả chặng, bạn code lại dự án theo thứ tự:

| Bước | File | Chặng |
|------|------|-------|
| 1 | `app/__init__.py` | (rỗng) |
| 2 | `labeling/__init__.py` | (rỗng) |
| 3 | `app/schemas.py` | 1 |
| 4 | `app/sources.py` | 2 |
| 5 | `labeling/prompt.py` | 3 |
| 6 | `labeling/qc.py` | 4 |
| 7 | `labeling/gemini_labeler.py` | 5 |
| 8 | `labeling/label_dataset.py` | 6 |
| 9 | `labeling/split_dataset.py` | 7 |
| 10 | `app/crawler.py` | 8+9 |
| 11 | `app/summarizer.py` | 10 |
| 12 | `app/main.py` | 11 |
| 13 | `app/templates/index.html` | 11 |
| 14 | `requirements.txt` | copy |
| 15 | `pyproject.toml` | copy |
| 16 | `.env.example` | copy |
| 17 | `Makefile` | copy |
| 18 | `README.md` | copy |
| 19 | `Dockerfile` + `docker-compose.yml` | copy |

**Tiêu chí hoàn thành:** Chạy được:
```bash
# Crawl
python -m app.crawler --mode labeling --source vnexpress --limit 5 --output data/raw/test.jsonl

# Label (cần GEMINI_API_KEYS)
python -m labeling.label_dataset --input data/raw/test.jsonl --output data/labeled/test.jsonl --limit 3

# Split
python -m labeling.split_dataset --input data/labeled/test.jsonl --output data/datasets/test

# Web demo
uvicorn app.main:app --reload
```

---

## Lịch Học Gợi Ý (8 tuần)

| Tuần | Chặng | Nội dung |
|------|-------|----------|
| 1 | 0-1 | Python nền tảng + schemas |
| 2 | 2-3 | Sources config + Prompt/Parser |
| 3 | 4 | QC rules (regex, fuzzy matching) |
| 4 | 5-6 | AI Studio labeler + label pipeline |
| 5 | 7 | Split dataset |
| 6 | 8-9 | Crawler (URL, SimHash, HTTP, RSS, extract) |
| 7 | 10 | ViT5 Summarizer (PEFT, tokenizer, batch) |
| 8 | 11 | FastAPI + HTML + tổng kết code lại dự án |

---

## Command Thực Tế Nên Nhớ

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env

# Crawl
python -m app.crawler --mode labeling --output data/raw/articles.jsonl
python -m app.crawler --mode labeling --source vnexpress --limit 10 --output data/raw/test.jsonl --verbose

# Label (AI Studio)
export GEMINI_API_KEYS=key1,key2,key3
python -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl --concurrency 5

# Split
python -m labeling.split_dataset --input data/labeled/labeled_articles.jsonl --output data/datasets/v2

# Web demo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lint
ruff check app/ labeling/
```
