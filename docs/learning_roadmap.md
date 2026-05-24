# Lộ Trình Học Để Tự Code Lại `vn-news-summarizer`

Tài liệu này dành cho người mới học. Mục tiêu: hiểu từng mảnh nhỏ rồi **tự code lại được toàn bộ dự án**, từng file, từng dòng.

**Nguyên tắc:**
- Mỗi chặng dạy một nhóm kiến thức.
- Có bài tập nhỏ (có lời giải) giúp bạn nắm kiến thức. Bài tập được chia nhỏ từ dễ lên khó.
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
| `labeling/batch_labeler.py` | 260 | 6B |
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
JSONL = mỗi dòng là 1 object JSON. Dự án dùng format này cho dữ liệu bài báo.

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

### Bài tập 0.1 — json.loads và json.dumps

**Bối cảnh:** Trước khi đọc/ghi file JSONL, cần hiểu cách Python chuyển dict ↔ JSON string.

**Yêu cầu:**
1. Tạo 1 dict Python: `{"title": "Tin A", "content": "Nội dung tiếng Việt"}`.
2. Dùng `json.dumps(dict, ensure_ascii=False)` để chuyển thành JSON string. In ra.
3. Dùng `json.loads(json_string)` để chuyển ngược lại thành dict. In ra.
4. Thử `json.dumps(dict)` (KHÔNG có `ensure_ascii=False`). Quan sát sự khác biệt.

**Đáp án:**

```python
import json

# Bước 1: Tạo dict
data = {"title": "Tin A", "content": "Nội dung tiếng Việt"}

# Bước 2: Dict → JSON string (giữ tiếng Việt)
json_str = json.dumps(data, ensure_ascii=False)
print(json_str)  # {"title": "Tin A", "content": "Nội dung tiếng Việt"}

# Bước 3: JSON string → Dict
loaded = json.loads(json_str)
print(loaded)     # {'title': 'Tin A', 'content': 'Nội dung tiếng Việt'}
print(loaded == data)  # True

# Bước 4: Không ensure_ascii=False → escape tiếng Việt
json_str_ascii = json.dumps(data)
print(json_str_ascii)  # {"title": "Tin A", "content": "N\u1ed9i dung ti\u1ebfng Vi\u1ec7t"}
```

### Bài tập 0.2 — Đọc ghi file JSONL

**Bối cảnh:** JSONL (JSON Lines) = mỗi dòng trong file là 1 JSON object. Ví dụ file `test.jsonl`:
```
{"title": "Tin A", "content": "abc"}
{"title": "Tin B", "content": "xyz"}
```

**Yêu cầu:**
1. Viết function `write_jsonl(path, rows)`:
   - Nhận `path` (kiểu `Path`) và `rows` (list các dict).
   - Tạo thư mục cha nếu chưa có (`path.parent.mkdir(parents=True, exist_ok=True)`).
   - Mở file để ghi, mỗi dict ghi 1 dòng JSON (dùng `ensure_ascii=False`).
2. Viết function `read_jsonl(path)`:
   - Nhận `path`, đọc file, mỗi dòng không rỗng → `json.loads` → thêm vào list.
   - Trả list các dict.
3. Test: ghi 2 dict ra file, đọc lại, assert bằng nhau.

**Đáp án:**

```python
import json
from pathlib import Path

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

# Test
rows = [{"title": "Tin A", "content": "Nội dung A"}, {"title": "Tin B", "content": "Nội dung B"}]
write_jsonl(Path("/tmp/test.jsonl"), rows)
loaded = read_jsonl(Path("/tmp/test.jsonl"))
assert loaded == rows
print("OK!")
```

### Bài tập 0.3 — argparse CLI cơ bản

**Bối cảnh:** Dự án dùng `argparse` để tạo CLI (command-line interface) cho crawler, labeler, splitter. Bạn cần biết cách nhận tham số từ command line.

**Yêu cầu:** Viết một script CLI đơn giản:
1. Nhận `--input` (kiểu Path, bắt buộc) — đường dẫn file JSONL.
2. Nhận `--limit` (kiểu int, mặc định None) — số dòng tối đa cần in.
3. Đọc file JSONL bằng `read_jsonl()` ở bài trước.
4. In ra `limit` dòng đầu (nếu `--limit` được truyền), hoặc tất cả dòng nếu không truyền.
5. Chạy thử: `python my_script.py --input /tmp/test.jsonl --limit 1`

**Đáp án:**

```python
import argparse
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

def main():
    parser = argparse.ArgumentParser(description="In JSONL")
    parser.add_argument("--input", type=Path, required=True, help="Đường dẫn file JSONL")
    parser.add_argument("--limit", type=int, default=None, help="Số dòng tối đa")
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    for row in rows[:args.limit]:  # rows[:None] = tất cả
        print(json.dumps(row, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### Bài tập 0.4 — Biến môi trường

**Bối cảnh:** Dự án đọc API key từ biến môi trường `GEMINI_API_KEYS` (nhiều key, phân cách bằng dấu phẩy) hoặc `GEMINI_API_KEY` (1 key). Bạn cần biết cách đọc và xử lý biến môi trường.

**Yêu cầu:** Viết function `get_keys()`:
1. Đọc `GEMINI_API_KEYS` từ environment. Nếu có → split bằng dấu phẩy, strip khoảng trắng, loại bỏ chuỗi rỗng, trả list.
2. Nếu `GEMINI_API_KEYS` rỗng → đọc `GEMINI_API_KEY`. Nếu có → trả list 1 phần tử.
3. Nếu cả hai đều không có → raise `RuntimeError` với thông báo rõ ràng.
4. Test: `os.environ["GEMINI_API_KEYS"] = "key1, key2, key3"` → `get_keys()` trả `["key1", "key2", "key3"]`.

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

# Test
os.environ["GEMINI_API_KEYS"] = "key1, key2, key3"
assert get_keys() == ["key1", "key2", "key3"]

del os.environ["GEMINI_API_KEYS"]
os.environ["GEMINI_API_KEY"] = "single_key"
assert get_keys() == ["single_key"]

del os.environ["GEMINI_API_KEY"]
try:
    get_keys()
    assert False, "Phải raise RuntimeError"
except RuntimeError as e:
    print(f"OK: {e}")
```

**So sánh dự án:** Mở `labeling/gemini_labeler.py`, function `_keys_from_env()` — logic giống hệt.

---

## Chặng 1 — Data Schemas (`app/schemas.py`)

**Mục tiêu:** hiểu `dataclass`, `Pydantic BaseModel`, `slots=True`, `frozen=True`. Code lại `app/schemas.py`.

### Lý thuyết

**1. `dataclass`:**
Python có thể tự tạo `__init__`, `__repr__`, `__eq__` cho class nếu bạn dùng decorator `@dataclass`:
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

p = Person("An", 25)      # Python tự tạo __init__
print(p)                    # Person(name='An', age=25) — tự tạo __repr__
print(p == Person("An", 25))  # True — tự tạo __eq__
```

**2. `slots=True`:** tiết kiệm bộ nhớ, không cho thêm attribute mới ngoài khai báo.
```python
@dataclass(slots=True)
class Person:
    name: str

p = Person("An")
p.x = 1  # ❌ AttributeError: 'Person' object has no attribute 'x'
```

**3. `frozen=True`:** immutable (không thể sửa sau khi tạo).
```python
@dataclass(slots=True, frozen=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
p.x = 3  # ❌ FrozenInstanceError
```
Dự án dùng `frozen=True` cho dữ liệu không cần thay đổi (bài báo crawl xong không sửa nữa).

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
- `dataclass`: dữ liệu nội bộ, không cần validate từ bên ngoài.
- `BaseModel`: dữ liệu từ bên ngoài (API response, JSON từ LLM) cần validate.

### Bài tập 1.1 — dataclass cơ bản

**Bối cảnh:** Khi crawl RSS, mỗi bài báo đầu tiên là một "ứng viên" (`ArticleCandidate`) với thông tin cơ bản từ RSS feed: nguồn, URL, tiêu đề. Một số trường có thể không có (ngày đăng, chuyên mục, tác giả).

**Yêu cầu:**
1. Tạo dataclass `ArticleCandidate` với `slots=True` và `frozen=True`.
2. Các field bắt buộc: `source` (str), `source_name` (str), `url` (str), `title` (str).
3. Các field tùy chọn (default `None`): `published_at` (datetime | None), `category` (str | None), `author` (str | None).
4. Test: tạo 1 instance, in ra, thử sửa attribute (phải bị lỗi).

**Gợi ý:** Import `datetime` từ module `datetime`. Các field có default phải đặt sau field không có default.

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

# Test
a = ArticleCandidate(source="vnexpress", source_name="VnExpress",
                     url="https://vnexpress.net/bai-1.html", title="Tin A")
print(a)  # ArticleCandidate(source='vnexpress', source_name='VnExpress', ...)
print(a.source)  # vnexpress

try:
    a.title = "Sửa"  # ❌ Frozen!
except Exception as e:
    print(f"Frozen: {e}")
```

### Bài tập 1.2 — dataclass với method

**Bối cảnh:** Sau khi crawl và extract nội dung, bài báo trở thành `CrawledArticle` với nhiều field hơn. Khi ghi ra file JSONL, ta không cần tất cả field (vd: `source_name`, `author`, `word_count`, `url_hash` không cần ghi). Method `to_jsonl_record()` chọn ra các field cần ghi.

**Yêu cầu:**
1. Tạo dataclass `CrawledArticle` (frozen, slots) với 11 field: `article_id` (int), `source` (str), `source_name` (str), `url` (str), `title` (str), `category` (str | None), `published_at` (str | None), `author` (str | None), `content_text` (str), `word_count` (int), `url_hash` (str).
2. Viết method `to_jsonl_record()` trả dict chỉ gồm 7 field: `article_id`, `source`, `url`, `title`, `category`, `published_at`, `content_text`.
3. Test: tạo instance, gọi `to_jsonl_record()`, kiểm tra dict trả về có đúng 7 key.

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

# Test
art = CrawledArticle(
    article_id=1, source="vnexpress", source_name="VnExpress",
    url="https://vnexpress.net/bai.html", title="Tin A",
    category="thoi_su", published_at="2024-01-01", author="NVA",
    content_text="Nội dung bài báo dài...", word_count=150, url_hash="abc123"
)
record = art.to_jsonl_record()
assert set(record.keys()) == {"article_id", "source", "url", "title", "category", "published_at", "content_text"}
assert "source_name" not in record  # Không ghi field này
assert "word_count" not in record   # Không ghi field này
print("OK:", record)
```

### Bài tập 1.3 — Pydantic BaseModel

**Bối cảnh:** API trả về JSON cho frontend. Pydantic BaseModel giúp validate và serialize dữ liệu. Dự án có 3 model API: `SummaryItem` (1 bài tóm tắt), `SummarizeResponse` (response chứa list bài), `HealthResponse` (health check).

**Yêu cầu:**
1. Tạo `SummaryItem(BaseModel)` với 5 field: `title` (str), `source` (str), `url` (str), `published_at` (str | None, default None), `summary` (str).
2. Tạo `SummarizeResponse(BaseModel)` với: `date` (str), `total` (int, dùng `Field(ge=0)` để đảm bảo >= 0), `items` (list[SummaryItem]).
3. Tạo `HealthResponse(BaseModel)` với: `status` (str), `version` (str).
4. Test: tạo `SummarizeResponse` với `total=-1` → phải bị `ValidationError`.

**Đáp án:**

```python
from pydantic import BaseModel, Field, ValidationError

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

# Test bình thường
resp = SummarizeResponse(
    date="2024-01-01", total=1,
    items=[SummaryItem(title="A", source="VnExpress", url="https://...", summary="Tóm tắt.")]
)
print(resp.model_dump_json(indent=2))

# Test validation: total < 0 → lỗi
try:
    SummarizeResponse(date="2024-01-01", total=-1, items=[])
    assert False
except ValidationError as e:
    print(f"OK, validation error: {e}")
```

### 🎯 Bài cuối chặng 1 — Code lại `app/schemas.py`

**Yêu cầu:** Gộp 3 bài tập trên vào 1 file `app/schemas.py` (64 dòng):
- Dòng đầu: `from __future__ import annotations`
- Import: `dataclass` từ `dataclasses`, `datetime` từ `datetime`, `BaseModel` và `Field` từ `pydantic`.
- 2 dataclass: `ArticleCandidate` (7 fields), `CrawledArticle` (11 fields + method).
- 3 BaseModel: `SummaryItem`, `SummarizeResponse`, `HealthResponse`.

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
Mỗi báo gọi chuyên mục khác nhau ("thời sự" vs "thoi-su" vs "xa-hoi"). Dự án map tất cả về một tên chuẩn.

**3. `field(default_factory=list)`:**
Khi default value là mutable (list, dict), phải dùng `default_factory`. Nếu viết `errors: list[str] = []` → tất cả instance chia sẻ cùng list (bug nghiêm trọng).

### Bài tập 2.1 — Constants và NewsSource

**Bối cảnh:** Crawler cần biết: user-agent gửi kèm request, delay giữa các request, timeout, số lần retry. Các giá trị này là constants.

**Yêu cầu:**
1. Định nghĩa 4 constants: `USER_AGENT` (chuỗi mô tả bot), `CRAWL_DELAY_SECONDS = 1.0`, `TIMEOUT_SECONDS = 20.0`, `MAX_RETRIES = 3`.
2. Tạo `NewsSource` dataclass (frozen, slots) với 6 field: `id` (str), `name` (str), `domain` (str), `rss` (list[str]), `enabled` (bool, default True), `max_items_per_feed` (int | None, default None).
3. Tạo 1 instance VnExpress với 9 RSS URLs, 1 instance Tuoi Tre với 8 RSS URLs.

**Đáp án:**

```python
from dataclasses import dataclass

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

vnexpress = NewsSource(
    id="vnexpress", name="VnExpress", domain="vnexpress.net",
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
)
tuoitre = NewsSource(
    id="tuoitre", name="Tuoi Tre Online", domain="tuoitre.vn",
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
)
print(f"VnExpress: {len(vnexpress.rss)} feeds, enabled={vnexpress.enabled}")
```

### Bài tập 2.2 — canonical_category

**Bối cảnh:** Mỗi báo dùng tên chuyên mục khác nhau:
- VnExpress: "thời sự", "kinh doanh"
- URL path: "thoi-su", "kinh-doanh", "xa-hoi"

Cần map tất cả về 1 tên chuẩn (ví dụ "thoi_su"). Cách làm: tạo dict `{"thoi_su": ["thời sự", "thoi su", "thoi-su", "xa-hoi", ...]}`, rồi tìm xem input khớp alias nào.

**Yêu cầu:**
1. Tạo dict `CANONICAL_CATEGORIES` với ít nhất 3 category: `thoi_su`, `kinh_doanh`, `cong_nghe`. Mỗi category có list alias.
2. Viết function `canonical_category(raw: str | None) -> str | None`:
   - Nếu `raw` là None hoặc rỗng → trả None.
   - Lowercase `raw`, duyệt qua từng (key, aliases) trong dict.
   - Nếu `raw` chứa alias hoặc alias chứa `raw` → trả key.
   - Không khớp → trả None.
3. Test các trường hợp.

**Đáp án:**

```python
CANONICAL_CATEGORIES = {
    "thoi_su": ["thời sự", "thoi su", "thoi-su", "thoi_su", "xã hội", "xa-hoi", "xa_hoi", "xa hoi"],
    "kinh_doanh": ["kinh doanh", "kinh-doanh", "kinh_doanh", "kinh tế", "kinh-te", "kinh_te", "kinh te"],
    "cong_nghe": ["công nghệ", "cong nghe", "cong-nghe", "cong_nghe", "so-hoa", "so_hoa", "khoa-hoc", "khoa_hoc"],
}

def canonical_category(raw: str | None) -> str | None:
    if not raw:
        return None
    needle = raw.lower()
    for key, aliases in CANONICAL_CATEGORIES.items():
        if any(alias in needle or needle in alias for alias in aliases):
            return key
    return None

# Test
assert canonical_category("thời sự") == "thoi_su"
assert canonical_category("kinh-doanh") == "kinh_doanh"
assert canonical_category("xa-hoi") == "thoi_su"
assert canonical_category(None) is None
assert canonical_category("") is None
assert canonical_category("unknown") is None
print("OK!")
```

### Bài tập 2.3 — field(default_factory=list) và CrawlStats

**Bối cảnh:** Khi crawl, cần theo dõi thống kê cho mỗi nguồn: bao nhiêu bài tìm thấy, bao nhiêu fetch thành công, bao nhiêu lỗi... Field `errors` là list các chuỗi lỗi.

**Yêu cầu:**
1. Tạo dataclass `CrawlStats` (slots=True, KHÔNG frozen vì cần sửa):
   - `discovered: int = 0`, `fetched: int = 0`, `extracted: int = 0`
   - `skipped_duplicate: int = 0`, `skipped_robots: int = 0`
   - `fetch_failed: int = 0`, `extract_failed: int = 0`
   - `errors: list[str] = field(default_factory=list)` ← quan trọng!
2. Test: tạo 2 instance CrawlStats, thêm error vào instance 1. Kiểm tra instance 2 không bị ảnh hưởng.
3. Giải thích tại sao không viết `errors: list[str] = []`.

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

# Test: 2 instance KHÔNG chia sẻ list
s1 = CrawlStats()
s2 = CrawlStats()
s1.errors.append("lỗi X")
s1.fetched += 10
assert s2.errors == []      # s2 không bị ảnh hưởng
assert s2.fetched == 0
print("OK! s1.errors:", s1.errors, "s2.errors:", s2.errors)

# Nếu viết sai: errors: list[str] = [] thì:
# s1.errors và s2.errors trỏ đến CÙNG 1 list → bug!
```

### Bài tập 2.4 — enabled_sources

**Bối cảnh:** Không phải nguồn nào cũng hoạt động tốt. Ví dụ Lao Dong bị lỗi nên `enabled=False`. Function `enabled_sources` lọc chỉ nguồn đang bật.

**Yêu cầu:**
1. Tạo `SOURCES` list chứa 3 NewsSource: 2 cái `enabled=True`, 1 cái `enabled=False`.
2. Viết function `enabled_sources(only: set[str] | None = None) -> list[NewsSource]`:
   - Lọc các source có `enabled=True`.
   - Nếu `only` không None → chỉ giữ source có `id` nằm trong `only`.
3. Test: `enabled_sources()` trả 2, `enabled_sources({"vnexpress"})` trả 1.

**Đáp án:**

```python
SOURCES = [
    NewsSource(id="vnexpress", name="VnExpress", domain="vnexpress.net", rss=["..."]),
    NewsSource(id="tuoitre", name="Tuoi Tre", domain="tuoitre.vn", rss=["..."]),
    NewsSource(id="laodong", name="Lao Dong", domain="laodong.vn", enabled=False, rss=["..."]),
]

def enabled_sources(only: set[str] | None = None) -> list[NewsSource]:
    return [s for s in SOURCES if s.enabled and (only is None or s.id in only)]

# Test
assert len(enabled_sources()) == 2  # laodong bị disabled
assert len(enabled_sources({"vnexpress"})) == 1
assert enabled_sources({"vnexpress"})[0].id == "vnexpress"
assert len(enabled_sources({"laodong"})) == 0  # disabled → không trả
print("OK!")
```

### 🎯 Bài cuối chặng 2 — Code lại `app/sources.py`

**Yêu cầu:** Tạo file `app/sources.py` (189 dòng) gồm:
- 4 constants: `USER_AGENT`, `CRAWL_DELAY_SECONDS`, `TIMEOUT_SECONDS`, `MAX_RETRIES`
- `NewsSource` dataclass (frozen, slots, 6 fields)
- `SOURCES` list — đủ 8 nguồn báo (vnexpress, tuoitre, thanhnien, vietnamnet, dantri, znews, vtcnews, laodong). Lưu ý: `laodong` có `enabled=False`, `vietnamnet` có `max_items_per_feed=100`.
- `CANONICAL_CATEGORIES` dict — đủ 8 categories (thoi_su, kinh_doanh, cong_nghe, the_thao, giai_tri, giao_duc, suc_khoe, the_gioi)
- `CrawlStats` dataclass (slots, mutable, dùng `field(default_factory=list)`)
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

**2. `GenerationParams`:** cấu hình gửi kèm mỗi request tới Gemini (temperature, max tokens, v.v.).

**3. `LabelOutput`:** Pydantic model validate output từ Gemini.

**4. `render_user_prompt`:** ghép dữ liệu bài báo vào template, cắt content nếu quá dài (tránh tốn token).

**5. `parse_label_json`:** parse JSON output robust — xử lý JSON lỗi, clamp confidence, xử lý refusal.

### Bài tập 3.1 — String template với .format()

**Bối cảnh:** Dự án dùng `str.format()` để ghép dữ liệu bài báo vào prompt template. Cần hiểu cách `.format()` hoạt động, đặc biệt với dấu `{{}}` để escape literal braces trong JSON schema.

**Yêu cầu:**
1. Tạo template string chứa placeholder `{title}` và `{content}`, đồng thời có literal JSON `{{"key": "value"}}`.
2. Gọi `.format(title="Tin A", content="Nội dung")` và in kết quả.
3. Giải thích: tại sao `{{` trở thành `{` sau format?

**Đáp án:**

```python
template = """Tiêu đề: {title}
Nội dung: {content}

Trả về JSON:
{{"summary": "...", "confidence": 0.0}}"""

result = template.format(title="Tin A", content="Nội dung bài báo")
print(result)
# Tiêu đề: Tin A
# Nội dung: Nội dung bài báo
#
# Trả về JSON:
# {"summary": "...", "confidence": 0.0}

# Giải thích: {{  → { sau format (escape), {title} → giá trị title
```

### Bài tập 3.2 — Cắt chuỗi tại ranh giới từ

**Bối cảnh:** Nội dung bài báo có thể rất dài (10000+ ký tự), tốn token khi gửi cho Gemini. Cần cắt tối đa 6000 ký tự. Nhưng không nên cắt giữa từ (ví dụ "Nguyễ" thay vì "Nguyễn"). Dùng `.rsplit(" ", 1)[0]` để cắt tại khoảng trắng cuối cùng.

**Yêu cầu:**
1. Viết function `truncate_at_word(text: str, max_chars: int) -> str`:
   - Nếu `len(text) <= max_chars` → trả nguyên.
   - Ngược lại: cắt `text[:max_chars]`, tìm khoảng trắng cuối cùng bằng `.rsplit(" ", 1)[0]`, thêm `" [...]"`.
2. Test với chuỗi ngắn (không cắt) và chuỗi dài (cắt đúng tại ranh giới từ).

**Đáp án:**

```python
def truncate_at_word(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + " [...]"

# Test: chuỗi ngắn → không cắt
assert truncate_at_word("Ngắn", 100) == "Ngắn"

# Test: chuỗi dài → cắt tại ranh giới từ
long_text = "Đây là một câu rất dài cần phải cắt bớt cho vừa"
result = truncate_at_word(long_text, 20)
print(repr(result))  # "Đây là một câu rất [...]"
assert "[...]" in result
assert len(result) < 30  # ngắn hơn nhiều so với gốc
assert not result.endswith("dà [...]")  # không cắt giữa từ
```

### Bài tập 3.3 — render_user_prompt hoàn chỉnh

**Bối cảnh:** Ghép tất cả lại: template + truncate + format.

**Yêu cầu:**
1. Định nghĩa `USER_TEMPLATE` — template chứa `{title}`, `{category}`, `{source}`, `{content_text}` và JSON schema với `{{}}`.
2. Viết `render_user_prompt(*, title, category, source, content_text, content_max_chars=6000)`:
   - Truncate `content_text` nếu dài hơn `content_max_chars` (dùng logic bài 3.2).
   - Gọi `USER_TEMPLATE.format(...)`.
3. Test: truyền content dài 12000 ký tự, kiểm tra output có `[...]` và ngắn hơn 7000 ký tự.

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

# Test
long_text = "từ " * 3000  # 12000 ký tự
result = render_user_prompt(title="Test", category="thoi_su", source="vnexpress", content_text=long_text)
assert "[...]" in result
assert len(result) < 7000
print(f"Độ dài output: {len(result)} ký tự. OK!")
```

### Bài tập 3.4 — LabelOutput Pydantic model

**Bối cảnh:** Gemini trả JSON, cần validate output. Field `confidence` phải trong [0.0, 1.0]. Field `refusal_reason` là None nếu AI đồng ý tóm tắt.

**Yêu cầu:**
1. Tạo `LabelOutput(BaseModel)` với:
   - `summary: str`
   - `key_entities: list[str] = Field(default_factory=list)`
   - `confidence: float = Field(default=0.0, ge=0.0, le=1.0)`
   - `refusal_reason: str | None = None`
2. Test: tạo bình thường, tạo thiếu summary (→ lỗi), tạo với confidence > 1.0 (→ lỗi).

**Đáp án:**

```python
from pydantic import BaseModel, Field, ValidationError

class LabelOutput(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    refusal_reason: str | None = None

# OK
out = LabelOutput(summary="Tóm tắt.", key_entities=["VN"], confidence=0.9)
print(out)

# Thiếu summary → lỗi
try:
    LabelOutput(confidence=0.5)
except ValidationError as e:
    print(f"Thiếu summary: {e}")

# confidence > 1.0 → lỗi (vì le=1.0)
try:
    LabelOutput(summary="X", confidence=1.5)
except ValidationError as e:
    print(f"confidence > 1.0: {e}")
```

### Bài tập 3.5 — parse_label_json robust

**Bối cảnh:** Gemini đôi khi trả JSON không hoàn hảo:
- JSON có newline trong string → `json.loads` strict mode bị lỗi, cần `strict=False`.
- `confidence` có khi trả 95.0 thay vì 0.95 → cần clamp về 1.0.
- Nếu AI từ chối tóm tắt: `summary=null` + `refusal_reason="not news"` → set `summary=""`.

**Yêu cầu:** Viết `parse_label_json(raw_text: str) -> LabelOutput`:
1. Thử `json.loads(raw_text)`. Nếu lỗi `JSONDecodeError` → thử `json.loads(raw_text, strict=False)`. Nếu vẫn lỗi → raise `ValueError`.
2. Nếu `confidence > 1.0` → set về `1.0`.
3. Nếu `summary is None` và có `refusal_reason` → set `summary = ""`.
4. Validate bằng `LabelOutput(**data)`. Nếu `ValidationError` → raise `ValueError`.

Test 3 trường hợp: bình thường, confidence > 1.0, refusal.

**Đáp án:**

```python
import json
from pydantic import ValidationError

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

# Test 1: Bình thường
out = parse_label_json('{"summary":"Tin A.","key_entities":["VN"],"confidence":0.9,"refusal_reason":null}')
assert out.summary == "Tin A."
assert out.confidence == 0.9

# Test 2: Confidence > 1.0 → clamp
out = parse_label_json('{"summary":"X.","key_entities":[],"confidence":95.0}')
assert out.confidence == 1.0

# Test 3: Refusal
out = parse_label_json('{"summary":null,"key_entities":[],"confidence":0.0,"refusal_reason":"not news"}')
assert out.summary == ""
assert out.refusal_reason == "not news"

print("Tất cả test pass!")
```

### 🎯 Bài cuối chặng 3 — Code lại `labeling/prompt.py`

**Yêu cầu:** Tạo file `labeling/prompt.py` (105 dòng):
- `PROMPT_VERSION = "1.2.0"`, `PROMPT_MODEL = "gemini-2.5-flash"`, `PROMPT_PROVIDER = "aistudio"`
- `SYSTEM_PROMPT` — full text prompt biên tập viên (xem trong dự án)
- `USER_TEMPLATE` — template có `{title}`, `{category}`, `{source}`, `{content_text}`
- `GenerationParams` dataclass (4 fields: temperature=0.2, top_p=0.9, max_output_tokens=4096, response_mime_type="application/json")
- `QcConfig` dataclass (5 fields: min_words=40, max_words=90, min_sentences=2, max_sentences=4, entity_fuzzy_min_ratio=0.85)
- `LabelOutput` BaseModel
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

**3. Regex lookbehind cho tách câu:**
```python
_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")
```
`(?<=...)` = lookbehind — split tại vị trí SAU dấu câu + trước khoảng trắng, nhưng giữ lại dấu câu.

**4. Fuzzy matching (rapidfuzz):**
`fuzz.partial_ratio("Nguyễn Văn A", "Ông Nguyễn Văn A cho biết...") ≈ 100` vì chuỗi ngắn nằm hoàn toàn trong chuỗi dài.

### Bài tập 4.1 — Unicode normalize + gộp whitespace

**Bối cảnh:** Text crawl từ web thường có whitespace thừa, dấu tiếng Việt không thống nhất. Cần normalize trước khi xử lý.

**Yêu cầu:**
1. Viết function `_norm(text: str) -> str`:
   - Nhận chuỗi, trả chuỗi đã NFC normalize + strip.
   - Nếu `text` rỗng hoặc None → trả `""`.
2. Viết function `_word_count(text: str) -> int`:
   - NFC normalize text, split bằng whitespace, đếm số từ.
3. Test: `_norm("  Tin  tức  ")` → `"Tin  tức"`, `_word_count("Tin tức hôm nay")` → 4.

**Đáp án:**

```python
import unicodedata

def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").strip()

def _word_count(text: str) -> int:
    return len(_norm(text).split())

# Test
assert _norm("  Tin  tức  ") == "Tin  tức"
assert _norm(None) == ""
assert _norm("") == ""
assert _word_count("Tin tức hôm nay") == 4
assert _word_count("") == 0
print("OK!")
```

### Bài tập 4.2 — Regex tách câu tiếng Việt

**Bối cảnh:** QC cần đếm câu trong summary (yêu cầu 2-4 câu). Câu kết thúc bằng `.`, `!`, `?`, hoặc `…` (Unicode `\u2026`). Dùng regex lookbehind `(?<=...)` để split nhưng giữ dấu câu.

**Yêu cầu:**
1. Tạo regex `_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")`.
2. Viết function `_sentences(text: str) -> list[str]`:
   - NFC normalize text (dùng `_norm`).
   - Split bằng `_SENT_SPLIT`.
   - Loại bỏ phần tử rỗng, strip mỗi phần tử.
3. Test: `_sentences("Câu một. Câu hai! Câu ba?")` → `["Câu một.", "Câu hai!", "Câu ba?"]`.

**Đáp án:**

```python
import re

_SENT_SPLIT = re.compile(r"(?<=[\.!?\u2026])\s+")

def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENT_SPLIT.split(_norm(text)) if part.strip()]

# Test
assert _sentences("Câu một. Câu hai! Câu ba?") == ["Câu một.", "Câu hai!", "Câu ba?"]
assert len(_sentences("Một câu duy nhất.")) == 1
assert _sentences("") == []
assert _sentences("Kết thúc bằng ellipsis\u2026 Câu tiếp.") == ["Kết thúc bằng ellipsis\u2026", "Câu tiếp."]
print("OK!")
```

### Bài tập 4.3 — Extract số từ text

**Bối cảnh:** QC kiểm tra: mọi con số trong summary có xuất hiện trong bài gốc không (tránh bịa số liệu). Bước đầu: extract tất cả token chứa chữ số.

**Yêu cầu:**
1. Tạo regex `_NUMERIC = re.compile(r"\S*\d[\S]*")` — token không-khoảng-trắng chứa ít nhất 1 chữ số.
2. Viết function `_numerics(text: str) -> list[str]`:
   - Dùng `_NUMERIC.finditer(text)` tìm tất cả match.
   - Mỗi match: lấy `.group(0)`, strip bỏ ký tự đặc biệt đầu/cuối: `".,;:%()[]{}"`
   - Nếu sau strip vẫn non-empty → thêm vào list.
3. Test: `_numerics("Có 1.500 người và 30% tăng trưởng")` → `["1.500", "30%"]`.

**Đáp án:**

```python
_NUMERIC = re.compile(r"\S*\d[\S]*")

def _numerics(text: str) -> list[str]:
    out: list[str] = []
    for match in _NUMERIC.finditer(text):
        token = match.group(0).strip(".,;:%()[]{}")
        if token:
            out.append(token)
    return out

# Test
assert _numerics("Có 1.500 người và 30% tăng trưởng") == ["1.500", "30%"]
assert _numerics("Không có số") == []
assert _numerics("Ngày 15/3/2024 có 2 sự kiện") == ["15/3/2024", "2"]
print("OK!")
```

### Bài tập 4.4 — Extract entity (tên riêng) từ text

**Bối cảnh:** Entity = chuỗi từ viết hoa liên tiếp (tên người, địa danh). Ví dụ: "Nguyễn Văn A", "Hà Nội". QC kiểm tra entity trong summary phải có trong bài gốc.

**Yêu cầu:**
1. Tạo chuỗi `_TITLE_CHARS` chứa tất cả ký tự hoa tiếng Việt: `"A-ZĐÁÀẢÃẠ..."` (xem trong dự án).
2. Tạo regex `_ENTITY = re.compile(rf"(?:[{_TITLE_CHARS}][\wÀ-ỹ]*(?:\s+[{_TITLE_CHARS}][\wÀ-ỹ]*)+)")`:
   - Match chuỗi 2+ từ liên tiếp, mỗi từ bắt đầu bằng chữ hoa.
3. Viết `_entities(text: str) -> list[str]`:
   - Tìm tất cả match, deduplicate (dùng set `seen`), trả list.
4. Test: `_entities("Ông Nguyễn Văn A tại Hà Nội")` → chứa "Nguyễn Văn" (hoặc tương tự).

**Đáp án:**

```python
_TITLE_CHARS = (
    "A-ZĐÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆ"
    "ÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ"
)
_ENTITY = re.compile(rf"(?:[{_TITLE_CHARS}][\wÀ-ỹ]*(?:\s+[{_TITLE_CHARS}][\wÀ-ỹ]*)+)")

def _entities(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for match in _ENTITY.finditer(text):
        entity = match.group(0).strip()
        if entity and entity not in seen:
            seen.add(entity)
            out.append(entity)
    return out

# Test
ents = _entities("Ông Nguyễn Văn A cho biết tại Hà Nội ngày 15/3")
print("Entities:", ents)
assert any("Nguyễn Văn" in e for e in ents)
assert any("Hà Nội" in e for e in ents)
```

### Bài tập 4.5 — _contains_numeric (kiểm tra số có trong source không)

**Bối cảnh:** Summary nói "1.500 người", cần kiểm tra bài gốc có "1.500" không. Nhưng bài gốc có thể viết "1500" (không có dấu chấm) hoặc "1 500" (khoảng trắng). Cần kiểm tra linh hoạt:
1. Exact match trước.
2. Collapse punctuation (thay dấu chấm, phẩy, khoảng trắng bằng space) rồi match.
3. Extract nhóm 3+ chữ số, kiểm tra từng nhóm có trong source.

**Yêu cầu:**
1. Tạo regex `_PUNCT_RE = re.compile(r"[\s\-\u2013\u2014\.\,;:\(\)\[\]\{\}/]+")` và `_DIGIT_GROUP = re.compile(r"\d{3,}")`.
2. Viết `_collapse_punct(text)`: thay tất cả ký tự khớp `_PUNCT_RE` bằng space, strip.
3. Viết `_contains_numeric(source, token)`:
   - `token in source` → True.
   - `_collapse_punct(token) in _collapse_punct(source)` → True.
   - Extract nhóm 3+ digit từ token, kiểm tra tất cả nhóm có trong source → True.
   - Không khớp → False.
4. Test: `_contains_numeric("Có 1500 người", "1.500")` → True (nhóm "1500" match).

**Đáp án:**

```python
_PUNCT_RE = re.compile(r"[\s\-\u2013\u2014\.\,;:\(\)\[\]\{\}/]+")
_DIGIT_GROUP = re.compile(r"\d{3,}")

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

# Test
assert _contains_numeric("Có 1.500 người", "1.500") == True      # exact match
assert _contains_numeric("Có 1500 người", "1.500") == True        # digit group "1500" match
assert _contains_numeric("Có 2000 người", "1.500") == False       # không match
assert _contains_numeric("GDP tăng 6,5%", "6,5%") == True         # exact
print("OK!")
```

### Bài tập 4.6 — _contains_entity (fuzzy matching)

**Bối cảnh:** Summary nói "Nguyễn Văn A", bài gốc viết "ông Nguyễn Văn A cho biết". Cần fuzzy match (không yêu cầu exact). Dùng `rapidfuzz.fuzz.partial_ratio` (hoặc fallback `difflib.SequenceMatcher`).

**Yêu cầu:**
1. Import rapidfuzz với fallback (xem lý thuyết chặng 4 phía trên):
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
2. Viết `_contains_entity(source, entity, *, min_ratio)`:
   - Exact match → True.
   - Collapse punct match → True.
   - `fuzz.partial_ratio(entity, source) >= min_ratio * 100` → True.
   - Bất kỳ token nào trong entity dài >= 4 ký tự mà có trong source → True.
   - Không khớp → False.
3. Test: `_contains_entity("Ông Nguyễn Văn A cho biết", "Nguyễn Văn A", min_ratio=0.85)` → True.

**Đáp án:**

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

# Test
assert _contains_entity("Ông Nguyễn Văn A cho biết", "Nguyễn Văn A", min_ratio=0.85) == True
assert _contains_entity("Bài về kinh tế", "Nguyễn Văn A", min_ratio=0.85) == False
print("OK!")
```

### Bài tập 4.7 — QcResult dataclass và run_qc

**Bối cảnh:** Ghép tất cả checks thành function `run_qc`. Input: `LabelOutput` (summary từ Gemini) + `source_text` (bài gốc) + `QcConfig` (ngưỡng). Output: `QcResult` với `passed` (bool) và danh sách `reasons` (tại sao fail).

**Yêu cầu:**
1. Tạo `QcResult` dataclass (slots=True) với: `passed` (bool), `reasons` (list[str]), `word_count` (int), `sentence_count` (int), `missing_numbers` (list[str]), `missing_entities` (list[str]). Thêm method `to_dict()`.
2. Viết `run_qc(*, output, source_text, cfg=None)`:
   - Check refusal → thêm reason `"llm_refusal:..."`.
   - Word count < min hoặc > max → thêm reason.
   - Sentence count < min hoặc > max → thêm reason.
   - Tìm số trong summary không có trong source → thêm reason.
   - Tìm entity trong summary không có trong source → thêm reason.
   - `passed = not reasons` (pass nếu không có reason nào).
3. Test: summary 50 từ, 2 câu, số đúng → pass. Summary 10 từ → fail too_short.

**Đáp án:**

```python
from dataclasses import dataclass, field
from labeling.prompt import LabelOutput, QcConfig

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
            "passed": self.passed, "reasons": self.reasons,
            "word_count": self.word_count, "sentence_count": self.sentence_count,
            "missing_numbers": self.missing_numbers, "missing_entities": self.missing_entities,
        }

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

# Test: summary hợp lệ
good = LabelOutput(summary="Ngày 15/3, Hà Nội tổ chức hội nghị kinh tế. " * 2 + "Có 500 đại biểu tham dự.", confidence=0.9)
source = "Ngày 15/3, Hà Nội tổ chức hội nghị kinh tế với 500 đại biểu"
result = run_qc(output=good, source_text=source)
print(f"Passed: {result.passed}, words: {result.word_count}, reasons: {result.reasons}")
```

### 🎯 Bài cuối chặng 4 — Code lại `labeling/qc.py`

**Yêu cầu:** Tạo file `labeling/qc.py` (153 dòng) gồm:
- Import `rapidfuzz` với fallback `difflib`
- Import `LabelOutput`, `QcConfig` từ `labeling.prompt`
- 6 regex constants: `_SENT_SPLIT`, `_NUMERIC`, `_PUNCT_RE`, `_DIGIT_GROUP`, `_TITLE_CHARS`, `_ENTITY`
- Helper functions: `_norm`, `_word_count`, `_sentences`, `_numerics`, `_collapse_punct`, `_contains_numeric`, `_entities`, `_contains_entity`
- `QcResult` dataclass + `to_dict`
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
    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
)
print(response.text)
```

**3. Key rotation:** khi key bị rate limit → tự chuyển sang key tiếp.

**4. Model fallback:** `gemini-2.5-flash` không khả dụng → thử `gemini-2.0-flash`.

**5. Error classification:** quota → thử key tiếp, transient → retry, model not found → thử model tiếp, fatal → dừng.

**6. Thread safety:** dùng `threading.Lock` bảo vệ dict `_clients`.

### Bài tập 5.1 — Exception classes

**Bối cảnh:** Dự án phân biệt 2 loại lỗi:
- `GeminiLLMError`: lỗi không thể retry (fatal) — ví dụ Gemini trả response blocked.
- `GeminiTransientError`: lỗi có thể retry (tạm thời) — ví dụ server 503.

Kế thừa `RuntimeError` để có thể bắt bằng `except RuntimeError`.

**Yêu cầu:**
1. Tạo 2 exception class: `GeminiLLMError(RuntimeError)` và `GeminiTransientError(RuntimeError)`.
2. Test: raise và catch mỗi loại, kiểm tra `isinstance`.

**Đáp án:**

```python
class GeminiLLMError(RuntimeError):
    """Lỗi không thể retry."""
    pass

class GeminiTransientError(RuntimeError):
    """Lỗi tạm thời, có thể retry."""
    pass

# Test
try:
    raise GeminiLLMError("Model blocked response")
except GeminiLLMError as e:
    print(f"Caught LLM error: {e}")
    assert isinstance(e, RuntimeError)  # cũng là RuntimeError

try:
    raise GeminiTransientError("503 server error")
except GeminiTransientError as e:
    print(f"Caught transient: {e}")
```

### Bài tập 5.2 — _keys_from_env

**Bối cảnh:** Đọc API key từ environment. Ưu tiên `GEMINI_API_KEYS` (nhiều key), fallback `GEMINI_API_KEY` (1 key). Nếu không có → raise `GeminiLLMError`.

**Yêu cầu:** Viết function `_keys_from_env() -> list[str]`:
1. Đọc `GEMINI_API_KEYS`, split bằng dấu phẩy, strip, lọc rỗng.
2. Nếu rỗng → đọc `GEMINI_API_KEY`.
3. Nếu cả hai rỗng → raise `GeminiLLMError`.

(Giống bài 0.4 nhưng dùng `GeminiLLMError` thay `RuntimeError`.)

**Đáp án:**

```python
import os

def _keys_from_env() -> list[str]:
    raw = os.environ.get("GEMINI_API_KEYS", "").strip()
    if not raw:
        single = os.environ.get("GEMINI_API_KEY", "").strip()
        if single:
            return [single]
        raise GeminiLLMError("Set GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY in your environment")
    return [k.strip() for k in raw.split(",") if k.strip()]
```

### Bài tập 5.3 — Error classification

**Bối cảnh:** Khi gọi API bị lỗi, cần phân loại để biết xử lý thế nào:
- Chứa "429", "quota", "rate limit" → `"quota"` (thử key tiếp)
- Chứa "503", "500", "timeout", "unavailable" → `"transient"` (retry)
- Chứa "not found", "does not exist" → `"model_not_found"` (thử model tiếp)
- Còn lại → `"fatal"` (dừng)

**Yêu cầu:** Viết `classify_error(exc: Exception) -> str` kiểm tra `str(exc).lower()` rồi trả loại lỗi. Test với các Exception khác nhau.

**Đáp án:**

```python
def classify_error(exc: Exception) -> str:
    err = str(exc).lower()
    if any(m in err for m in ("429", "resource has been exhausted", "quota", "rate limit", "too many requests")):
        return "quota"
    if any(m in err for m in ("deadline", "unavailable", "internal", "timeout", "503", "500")):
        return "transient"
    if "not found" in err or "does not exist" in err or "invalid" in err:
        return "model_not_found"
    return "fatal"

# Test
assert classify_error(Exception("429 Too Many Requests")) == "quota"
assert classify_error(Exception("resource has been exhausted")) == "quota"
assert classify_error(Exception("503 Service Unavailable")) == "transient"
assert classify_error(Exception("model gemini-3.0 not found")) == "model_not_found"
assert classify_error(Exception("unexpected error XYZ")) == "fatal"
print("OK!")
```

### Bài tập 5.4 — Per-call key iteration (giả lập, không cần API thật)

**Bối cảnh:** Nhiều thread gọi API cùng lúc. Nếu dùng shared index (ví dụ `self._current_key_idx`) → race condition. Giải pháp: mỗi lần gọi, copy danh sách key ra biến local rồi iterate.

**Yêu cầu:**
1. Viết function `try_all_keys_and_models(keys, models, call_fn)`:
   - `call_fn(key, model)` → trả kết quả hoặc raise exception.
   - Duyệt qua từng model, trong mỗi model duyệt qua từng key.
   - Nếu `call_fn` raise `QuotaError` → thử key tiếp.
   - Nếu `call_fn` raise `ModelNotFoundError` → break, thử model tiếp.
   - Nếu thành công → return kết quả.
   - Hết tất cả → raise RuntimeError.
2. Test với `fake_call` mà key1 bị quota, model1 bị not found ở key2, model2+key1 quota, model2+key2 thành công.

**Đáp án:**

```python
class QuotaError(Exception):
    pass

class ModelNotFoundError(Exception):
    pass

def try_all_keys_and_models(keys, models, call_fn):
    last_exc = None
    for model in models:
        for key in keys:
            try:
                return call_fn(key, model)
            except QuotaError as e:
                last_exc = e
                continue  # thử key tiếp
            except ModelNotFoundError as e:
                last_exc = e
                break  # thử model tiếp
    raise RuntimeError(f"All models/keys exhausted. Last: {last_exc}")

# Test
def fake_call(key, model):
    if model == "m1" and key == "k1":
        raise QuotaError("k1 quota exhausted")
    if model == "m1" and key == "k2":
        raise ModelNotFoundError("m1 not found")
    if model == "m2" and key == "k1":
        raise QuotaError("k1 quota exhausted")
    if model == "m2" and key == "k2":
        return f"Success with {model}+{key}"
    raise RuntimeError("unexpected")

result = try_all_keys_and_models(["k1", "k2"], ["m1", "m2"], fake_call)
assert result == "Success with m2+k2"
print(f"OK: {result}")
```

### Bài tập 5.5 — Thread-safe client cache

**Bối cảnh:** Tạo `genai.Client` tốn thời gian. Cache client theo API key. Nhưng nhiều thread có thể gọi cùng lúc → dùng `threading.Lock` bảo vệ dict.

**Yêu cầu:**
1. Viết class `ClientCache`:
   - `__init__`: tạo `_clients: dict = {}` và `_lock = threading.Lock()`.
   - `get_client(api_key)`: lock → nếu key chưa có trong dict → tạo mới (giả lập bằng dict `{"key": api_key}`) → return.
2. Test: gọi `get_client("k1")` 2 lần → trả cùng object (cache).

**Đáp án:**

```python
import threading

class ClientCache:
    def __init__(self):
        self._clients: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get_client(self, api_key: str) -> dict:
        with self._lock:
            if api_key not in self._clients:
                # Giả lập: trong dự án thật dùng genai.Client(api_key=api_key)
                self._clients[api_key] = {"key": api_key, "type": "genai.Client"}
            return self._clients[api_key]

# Test
cache = ClientCache()
c1 = cache.get_client("key_abc")
c2 = cache.get_client("key_abc")
assert c1 is c2  # cùng object (cache)
c3 = cache.get_client("key_xyz")
assert c3 is not c1  # key khác → object khác
print("OK! Cache hoạt động.")
```

### Bài tập 5.6 — Retry với tenacity

**Bối cảnh:** Lỗi transient (503, timeout) có thể tự hết sau vài giây. Dùng `tenacity` để retry tự động với exponential backoff (đợi 2s, 4s, 8s, ...).

**Yêu cầu:**
1. Viết function `call_with_retry(fn)` dùng tenacity decorator:
   - Chỉ retry `GeminiTransientError`.
   - Exponential backoff: min=2s, max=60s.
   - Tối đa 6 lần.
   - `GeminiLLMError` → dừng ngay (không retry).
2. Test: function fail 2 lần `GeminiTransientError` rồi thành công → phải trả kết quả.

**Đáp án:**

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

attempt_count = 0

@retry(
    reraise=True,
    retry=retry_if_exception_type(GeminiTransientError),
    wait=wait_exponential(multiplier=0.01, min=0.01, max=0.1),  # nhanh cho test
    stop=stop_after_attempt(6),
)
def call_with_retry():
    global attempt_count
    attempt_count += 1
    if attempt_count <= 2:
        raise GeminiTransientError(f"503 at attempt {attempt_count}")
    return "Success!"

attempt_count = 0
result = call_with_retry()
assert result == "Success!"
assert attempt_count == 3
print(f"OK! Retry {attempt_count - 1} lần rồi thành công.")
```

### 🎯 Bài cuối chặng 5 — Code lại `labeling/gemini_labeler.py`

**Yêu cầu:** Tạo file `labeling/gemini_labeler.py` (182 dòng) gồm:
- Module docstring
- `DEFAULT_MODEL_CHAIN = ["gemini-2.5-flash", "gemini-2.0-flash"]`
- `GeminiLLMError`, `GeminiTransientError` exception classes
- `OverrideFn` type alias: `Callable[[str, str], str]`
- `GeminiLabeler` class:
  - `__init__` (api_keys, model_chain, params, override_callable)
  - `_get_client` (thread-safe)
  - `generate` (tenacity retry, per-call local iteration, error classification, `except GeminiLLMError: raise` trước `except Exception`)
- `_keys_from_env()` function

**Kiểm tra:** So với `labeling/gemini_labeler.py` trong dự án — phải giống 100%.

---

## Chặng 6 — Label Dataset Pipeline (`labeling/label_dataset.py`)

**Mục tiêu:** hiểu asyncio.to_thread, semaphore, pipeline orchestration. Code lại `labeling/label_dataset.py`.

### Lý thuyết

**1. `asyncio.to_thread`:** chạy sync function trong thread pool, không block event loop.
**2. `asyncio.Semaphore`:** giới hạn concurrent requests.
**3. `asyncio.gather`:** chạy nhiều coroutine đồng thời.

### Bài tập 6.1 — asyncio.to_thread cơ bản

**Bối cảnh:** `GeminiLabeler.generate()` là sync function (blocking I/O — chờ HTTP response từ Gemini). Trong async context, nếu gọi trực tiếp → block toàn bộ event loop. Dùng `asyncio.to_thread` để chạy trong thread pool.

**Yêu cầu:**
1. Tạo sync function `slow_generate(text)` giả lập API call (sleep 0.1s, return kết quả).
2. Tạo async function `async_generate(text)` gọi `slow_generate` qua `asyncio.to_thread`.
3. Dùng `asyncio.run` để test.

**Đáp án:**

```python
import asyncio
import time

def slow_generate(text: str) -> str:
    """Giả lập API call (sync, blocking)."""
    time.sleep(0.1)
    return f"Summary of: {text[:30]}"

async def async_generate(text: str) -> str:
    """Wrap sync function bằng to_thread."""
    return await asyncio.to_thread(slow_generate, text)

# Test
result = asyncio.run(async_generate("Bài báo dài về kinh tế Việt Nam"))
print(result)  # Summary of: Bài báo dài về kinh tế Việt Na
```

### Bài tập 6.2 — asyncio.Semaphore giới hạn concurrency

**Bối cảnh:** Nếu gọi 100 bài cùng lúc, Gemini sẽ rate limit. Semaphore giới hạn chỉ N request đồng thời.

**Yêu cầu:**
1. Tạo `asyncio.Semaphore(2)` (tối đa 2 concurrent).
2. Tạo async function `limited_generate(text, sem)`: `async with sem:` rồi gọi `asyncio.to_thread(slow_generate, text)`.
3. Chạy 5 task cùng lúc bằng `asyncio.gather`. Đo thời gian: phải > 0.2s (vì 5 task, semaphore=2, mỗi task 0.1s → ít nhất 3 batch).

**Đáp án:**

```python
async def limited_generate(text: str, sem: asyncio.Semaphore) -> str:
    async with sem:
        return await asyncio.to_thread(slow_generate, text)

async def main():
    sem = asyncio.Semaphore(2)
    texts = [f"Bài {i}" for i in range(5)]
    start = time.monotonic()
    results = await asyncio.gather(*[limited_generate(t, sem) for t in texts])
    elapsed = time.monotonic() - start
    print(f"{len(results)} results in {elapsed:.2f}s")
    assert len(results) == 5
    assert elapsed >= 0.2  # 5 tasks / 2 concurrent = 3 batches * 0.1s

asyncio.run(main())
```

### Bài tập 6.3 — _label_one với error handling

**Bối cảnh:** Mỗi bài báo được label bởi `_label_one`. Nếu Gemini lỗi, KHÔNG crash toàn pipeline — trả row với `summary=""`, `qc_passed=False`.

**Yêu cầu:**
1. Viết async function `_label_one(row, *, labeler, semaphore)`:
   - Gọi `render_user_prompt(...)` từ dữ liệu row.
   - `async with semaphore:` gọi `asyncio.to_thread(labeler.generate, ...)`.
   - Parse JSON, chạy QC.
   - Trả dict gồm: `{**row, "summary": ..., "key_entities": ..., "confidence": ..., "refusal_reason": ..., "prompt_version": ..., "qc_passed": ..., "qc_details": ...}`.
   - Nếu catch `(GeminiLLMError, GeminiTransientError, ValueError)` → trả dict với `summary=""`, `qc_passed=False`.
2. Test: truyền fake labeler raise GeminiLLMError → kiểm tra output có `qc_passed=False`.

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

**Yêu cầu:** Tạo file `labeling/label_dataset.py` (133 dòng) gồm:
- `read_jsonl`, `write_jsonl` functions
- `_label_one(row, labeler, semaphore)` async function
- `label_rows(rows, concurrency, limit, labeler)` async function
- `_build_parser()` → argparse (--input, --output, --limit, --concurrency)
- `_run_cli(args)` async function
- `main(argv)` function (bắt KeyboardInterrupt)

**Kiểm tra:** So với `labeling/label_dataset.py` trong dự án — phải giống 100%.

---

## Chặng 6B — Batch Labeling với Rate Limit (`labeling/batch_labeler.py`)

**Mục tiêu:** hiểu rate limiting, key rotation, resumable processing, ước tính tài nguyên. Code lại `labeling/batch_labeler.py`.

### Lý thuyết

**1. Tại sao cần batch labeling?**
Chặng 6 dùng `asyncio.gather` gọi đồng thời — hoạt động tốt với vài trăm bài và key trả phí. Nhưng free-tier AI Studio có giới hạn:
- **RPM** (Requests Per Minute): tối đa 15 req/phút cho `gemini-3.1-flash-lite`.
- **RPD** (Requests Per Day): tối đa 500 req/ngày **per project**.
- Rate limit tính per project, không per API key. Mỗi key từ project khác = quota riêng.

Với 2810 bài, nếu gọi không kiểm soát → bị block ngay. Cần batch labeler thông minh.

**2. Chiến lược:**
- **Delay giữa requests:** `60 / RPM = 4 giây` → đảm bảo không vượt 15 RPM.
- **Key rotation round-robin:** phân bổ đều requests qua các key (project khác nhau).
- **Daily budget tracking:** mỗi key tối đa 450 req/ngày (safe margin < 500 RPD).
- **Resumable:** ghi kết quả từng dòng, restart tự skip bài đã xong.

**3. Ước tính tài nguyên:**
```
Dataset: 2810 bài
Model: gemini-3.1-flash-lite (15 RPM, 500 RPD/project)
Nếu 9 keys: 9 × 450 = 4,050 req/ngày → label hết trong 1 ngày
Thời gian chạy: 2810 × 4.5s delay ≈ 3.5 giờ
```

**4. `dataclass` cho config:**
```python
@dataclass(slots=True)
class BatchConfig:
    batch_size: int = 50
    delay_between_requests: float = 4.5
    max_per_key_per_day: int = 450
```

**5. Incremental write (append mode):**
```python
# Ghi từng row ngay khi xong — không mất dữ liệu nếu crash
with path.open("a", encoding="utf-8") as fh:  # "a" = append
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
```

### Bài tập 6B.1 — KeyUsageTracker

**Bối cảnh:** Mỗi key có budget 450 req/ngày. Cần track đã dùng bao nhiêu và tìm key còn quota.

**Yêu cầu:**
1. Tạo `KeyUsageTracker` dataclass với:
   - `daily_counts: dict[str, int]` — đếm số lần dùng mỗi key (key=index dạng str).
   - `budget_per_key: int = 450`.
2. Method `can_use(key_index: int) -> bool`: True nếu chưa vượt budget.
3. Method `record_use(key_index: int)`: tăng count.
4. Method `get_next_available(total_keys, start) -> int | None`: round-robin tìm key còn quota.
5. Method `total_remaining(total_keys) -> int`: tổng capacity còn lại.
6. Test: 3 keys, budget=2, dùng hết key 0 → `get_next_available` trả key 1.

**Đáp án:**

```python
from dataclasses import dataclass, field

@dataclass
class KeyUsageTracker:
    daily_counts: dict[str, int] = field(default_factory=dict)
    budget_per_key: int = 450

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

# Test
tracker = KeyUsageTracker(budget_per_key=2)
tracker.record_use(0)
tracker.record_use(0)
assert not tracker.can_use(0)  # key 0 đã hết budget
assert tracker.can_use(1)      # key 1 còn
assert tracker.get_next_available(3, start=0) == 1  # skip key 0, trả key 1
assert tracker.total_remaining(3) == 4  # key1: 2 + key2: 2 = 4
print("OK!")
```

### Bài tập 6B.2 — Resume: load existing article_ids

**Bối cảnh:** Nếu script crash giữa chừng (mất mạng, Ctrl+C), khi chạy lại cần skip bài đã label. Đọc output JSONL lấy tất cả `article_id` đã có.

**Yêu cầu:**
1. Viết `_load_existing_ids(output_path: Path) -> set[int]`:
   - Nếu file không tồn tại → trả `set()`.
   - Đọc mỗi dòng, parse JSON, lấy `article_id`, thêm vào set.
   - Nếu dòng bị lỗi JSON → skip (file có thể bị cắt giữa chừng).
2. Test: ghi 3 dòng JSONL, đọc lại, assert trả đúng 3 ids.

**Đáp án:**

```python
import json
from pathlib import Path

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
                    continue  # skip dòng bị lỗi
    return ids

# Test
test_path = Path("/tmp/test_resume.jsonl")
test_path.write_text(
    '{"article_id": 1, "summary": "A"}\n'
    '{"article_id": 5, "summary": "B"}\n'
    '{"article_id": 10, "summary": "C"}\n'
    'invalid json line\n',  # dòng lỗi — phải skip
    encoding="utf-8",
)
ids = _load_existing_ids(test_path)
assert ids == {1, 5, 10}
assert _load_existing_ids(Path("/tmp/nonexistent.jsonl")) == set()
print("OK!")
```

### Bài tập 6B.3 — Incremental append JSONL

**Bối cảnh:** Thay vì ghi tất cả cuối cùng (mất hết nếu crash), ghi ngay mỗi kết quả.

**Yêu cầu:**
1. Viết `_append_jsonl(path: Path, row: dict)`:
   - Tạo thư mục cha nếu chưa có.
   - Mở file mode `"a"` (append), ghi 1 dòng JSON + `"\n"`.
2. Test: append 3 rows, đọc lại file, assert có 3 dòng đúng.

**Đáp án:**

```python
def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False))
        fh.write("\n")

# Test
out = Path("/tmp/test_append.jsonl")
out.unlink(missing_ok=True)
_append_jsonl(out, {"article_id": 1, "summary": "Tin A"})
_append_jsonl(out, {"article_id": 2, "summary": "Tin B"})
_append_jsonl(out, {"article_id": 3, "summary": "Tin C"})

lines = out.read_text(encoding="utf-8").strip().split("\n")
assert len(lines) == 3
assert json.loads(lines[0])["article_id"] == 1
assert json.loads(lines[2])["summary"] == "Tin C"
print("OK!")
```

### Bài tập 6B.4 — asyncio.sleep cho rate limiting

**Bối cảnh:** Free tier cho 15 RPM. Delay 4.5s giữa requests đảm bảo ~13 req/phút (safe margin). Dùng `await asyncio.sleep(delay)` để không block event loop.

**Yêu cầu:**
1. Viết async function `rate_limited_calls(items, delay)`:
   - Lặp qua items, mỗi item gọi 1 async task giả lập.
   - `await asyncio.sleep(delay)` giữa mỗi call.
   - Trả list kết quả.
2. Đo thời gian: 5 items, delay=0.5s → tổng >= 2.0s (4 delays).

**Đáp án:**

```python
import asyncio
import time

async def fake_api_call(item: str) -> str:
    await asyncio.sleep(0.05)  # giả lập API latency
    return f"result:{item}"

async def rate_limited_calls(items: list[str], delay: float) -> list[str]:
    results = []
    for item in items:
        result = await fake_api_call(item)
        results.append(result)
        await asyncio.sleep(delay)  # rate limit delay
    return results

async def main():
    items = [f"article_{i}" for i in range(5)]
    start = time.monotonic()
    results = await rate_limited_calls(items, delay=0.5)
    elapsed = time.monotonic() - start
    assert len(results) == 5
    assert elapsed >= 2.0  # 5 items × 0.5s delay (cuối cùng cũng delay)
    print(f"5 items in {elapsed:.2f}s (rate limited). OK!")

asyncio.run(main())
```

### Bài tập 6B.5 — Ước tính tài nguyên

**Bối cảnh:** Trước khi chạy labeling, cần ước tính: bao nhiêu key, bao nhiêu ngày, bao lâu mỗi ngày?

**Yêu cầu:**
1. Viết function `estimate_resources(total_articles, num_keys, rpd_per_key, delay_seconds)`:
   - `daily_capacity = num_keys * rpd_per_key`
   - `days_needed = ceil(total_articles / daily_capacity)`
   - `hours_per_day = min(total_articles, daily_capacity) * delay_seconds / 3600`
   - Trả dict với 3 giá trị trên.
2. Test: 2810 bài, 9 keys, 450 RPD, 4.5s delay.

**Đáp án:**

```python
import math

def estimate_resources(
    total_articles: int, num_keys: int, rpd_per_key: int, delay_seconds: float
) -> dict:
    daily_capacity = num_keys * rpd_per_key
    days_needed = math.ceil(total_articles / daily_capacity)
    articles_per_day = min(total_articles, daily_capacity)
    hours_per_day = articles_per_day * delay_seconds / 3600
    return {
        "daily_capacity": daily_capacity,
        "days_needed": days_needed,
        "hours_per_day": round(hours_per_day, 1),
    }

# Test: dự án thực tế
result = estimate_resources(2810, num_keys=9, rpd_per_key=450, delay_seconds=4.5)
print(result)
# {'daily_capacity': 4050, 'days_needed': 1, 'hours_per_day': 3.5}
assert result["days_needed"] == 1
assert result["daily_capacity"] == 4050
assert 3.0 <= result["hours_per_day"] <= 4.0

# Test: ít key hơn
result2 = estimate_resources(2810, num_keys=3, rpd_per_key=450, delay_seconds=4.5)
assert result2["days_needed"] == 3  # 3*450=1350/day, 2810/1350 = 2.08 → 3 ngày
print("OK!")
```

### 🎯 Bài cuối chặng 6B — Code lại `labeling/batch_labeler.py`

**Yêu cầu:** Tạo file `labeling/batch_labeler.py` gồm:
- Constants: `MODEL = "gemini-3.1-flash-lite"`, `RPM = 15`, `RPD_PER_KEY = 500`, `SAFE_DELAY = 4.5`, `SAFE_RPD_BUDGET = 450`
- `BatchConfig` dataclass (3 fields: batch_size, delay_between_requests, max_per_key_per_day)
- `KeyUsageTracker` dataclass (4 methods: can_use, record_use, get_next_available, total_remaining)
- `read_jsonl`, `_load_existing_ids`, `_append_jsonl` I/O helpers
- `_label_one(article, labeler)` async function
- `batch_label(input_path, output_path, *, config, api_keys, limit)` async function — core logic
- `_keys_from_env()` helper
- `_build_parser()`, `_run_cli(args)`, `main(argv)` CLI

**Cách chạy:**
```bash
export GEMINI_API_KEYS=key1,key2,key3,...
python -m labeling.batch_labeler \
    --input data/raw/articles.jsonl \
    --output data/labeled/labeled_articles.jsonl \
    --limit 100
```

**Kiểm tra:** So với `labeling/batch_labeler.py` trong dự án — phải giống 100%.

---

## Chặng 7 — Split Dataset (`labeling/split_dataset.py`)

**Mục tiêu:** hiểu hash-based deterministic split, JSONL export. Code lại `labeling/split_dataset.py`.

### Lý thuyết

**Deterministic split:** dùng SHA-256 hash của `article_id` để quyết định article vào train/val/test. Cùng `article_id` luôn vào cùng split, không cần random state.

### Bài tập 7.1 — SHA-256 hash cơ bản

**Bối cảnh:** Python có module `hashlib` tính SHA-256. Output là bytes, byte đầu tiên (0-255) dùng để chia bucket.

**Yêu cầu:**
1. Tính SHA-256 của chuỗi `"vn-news-v1:42"` (salt + article_id).
2. Lấy byte đầu tiên: `digest[0]`.
3. In giá trị (0-255). Chạy nhiều lần → luôn cùng giá trị (deterministic).

**Đáp án:**

```python
import hashlib

text = "vn-news-v1:42"
digest = hashlib.sha256(text.encode()).digest()
bucket = digest[0]
print(f"Byte đầu tiên: {bucket}")  # Luôn cùng giá trị
print(f"Chạy lại: {hashlib.sha256(text.encode()).digest()[0]}")  # Giống!
```

### Bài tập 7.2 — split_bucket

**Bối cảnh:** Dùng byte đầu tiên (0-255) chia: `< 26` → test (~10%), `< 52` → val (~10%), còn lại → train (~80%).

**Yêu cầu:**
1. Viết `split_bucket(article_id: int, *, salt: str = "vn-news-v1") -> SplitName`:
   - Tính SHA-256 của `f"{salt}:{article_id}"`.
   - Byte đầu tiên `< 26` → `"test"`, `< 52` → `"val"`, còn lại → `"train"`.
2. Kiểm tra deterministic: `split_bucket(1) == split_bucket(1)`.
3. Kiểm tra phân bố: 1000 article → đa số vào train.

**Đáp án:**

```python
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

# Test deterministic
assert split_bucket(1) == split_bucket(1)
assert split_bucket(100) == split_bucket(100)

# Test phân bố
from collections import Counter
dist = Counter(split_bucket(i) for i in range(1000))
print(dist)  # Counter({'train': ~800, 'test': ~100, 'val': ~100})
assert dist["train"] > dist["val"]
assert dist["train"] > dist["test"]
```

### Bài tập 7.3 — dataset_record và split_rows

**Bối cảnh:** Từ labeled JSONL (nhiều field), chọn các field cần cho training. Lọc bỏ row `qc_passed=False` hoặc thiếu content/summary.

**Yêu cầu:**
1. Viết `dataset_record(row)` chọn 9 fields cần thiết (xem dự án).
2. Viết `split_rows(rows)` lọc + chia train/val/test.
3. Test: 3 rows, 1 row `qc_passed=False` → bị loại.

**Đáp án:**

```python
def dataset_record(row: dict) -> dict:
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

def split_rows(rows):
    splits = {"train": [], "val": [], "test": []}
    for row in rows:
        if row.get("qc_passed") is False:
            continue
        record = dataset_record(row)
        if not record["content_text"] or not record["summary"]:
            continue
        splits[split_bucket(int(record["article_id"]))].append(record)
    return splits

# Test
rows = [
    {"article_id": 1, "source": "vn", "content_text": "abc", "summary": "X.", "qc_passed": True},
    {"article_id": 2, "source": "vn", "content_text": "def", "summary": "Y.", "qc_passed": True},
    {"article_id": 3, "source": "vn", "content_text": "ghi", "summary": "", "qc_passed": False},
]
splits = split_rows(rows)
total = sum(len(v) for v in splits.values())
assert total == 2  # row 3 bị loại (qc_passed=False và summary rỗng)
print(f"Splits: {{{k}: {len(v)} for k, v in splits.items()}}}")
```

### 🎯 Bài cuối chặng 7 — Code lại `labeling/split_dataset.py`

**Yêu cầu:** Tạo file `labeling/split_dataset.py` (100 dòng) gồm:
- `SplitName`, `EXPECTED_V2_COUNTS`
- `split_bucket`, `read_jsonl`, `write_jsonl`, `dataset_record`, `split_rows`, `export_splits`
- `_build_parser` (--input, --output, --check-v2-counts)
- `main(argv)` function

**Kiểm tra:** So với `labeling/split_dataset.py` trong dự án — phải giống 100%.

---

## Chặng 8 — Crawler phần 1: URL, Text, HTTP (`app/crawler.py` dòng 1-250)

**Mục tiêu:** hiểu URL canonicalization, SimHash, text normalization, robots.txt, polite HTTP client.

### Lý thuyết

**1. URL canonicalization:** cùng 1 bài nhưng nhiều URL variant (có/không `utm_source`, port mặc định, trailing slash). Cần chuẩn hóa.

**2. SimHash:** phát hiện bài gần trùng (near-duplicate). 2 bài có Hamming distance <= 3 trên hash 64-bit → coi là trùng.

**3. PoliteClient:** HTTP client tôn trọng server: per-host lock (1 request/host/thời điểm), crawl delay, retry khi 429/5xx.

**4. robots.txt:** kiểm tra xem bot có được phép crawl URL không.

### Bài tập 8.1 — urlsplit và urlunsplit

**Bối cảnh:** Python có `urllib.parse.urlsplit` tách URL thành 5 phần: scheme, netloc, path, query, fragment. `urlunsplit` ghép lại. Đây là nền tảng của `canonicalize_url`.

**Yêu cầu:**
1. Import `urlsplit` và `urlunsplit` từ `urllib.parse`.
2. Split URL `"https://vnexpress.net/bai.html?utm_source=fb&a=1"` thành 5 phần. In từng phần.
3. Ghép lại bằng `urlunsplit`. Kiểm tra giống URL gốc.

**Đáp án:**

```python
from urllib.parse import urlsplit, urlunsplit

url = "https://vnexpress.net/bai.html?utm_source=fb&a=1"
parts = urlsplit(url)
print(f"scheme: {parts.scheme}")    # https
print(f"netloc: {parts.netloc}")    # vnexpress.net
print(f"path: {parts.path}")        # /bai.html
print(f"query: {parts.query}")      # utm_source=fb&a=1
print(f"fragment: {parts.fragment}") # (rỗng)

rebuilt = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
print(f"Rebuilt: {rebuilt}")
```

### Bài tập 8.2 — Lọc tracking params từ query string

**Bối cảnh:** URL thường chứa tracking params (`utm_source`, `fbclid`, `gclid`) không liên quan đến nội dung. Cần loại bỏ khi canonicalize.

**Yêu cầu:**
1. Dùng `parse_qsl(query)` tách query thành list `(key, value)`.
2. Lọc bỏ key bắt đầu bằng: `"utm_"`, `"fbclid"`, `"gclid"`, `"ref"`.
3. Sort theo key (deterministic).
4. Dùng `urlencode(pairs)` ghép lại.
5. Test: `"utm_source=fb&a=1&z=2"` → `"a=1&z=2"`.

**Đáp án:**

```python
from urllib.parse import parse_qsl, urlencode

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "ref")

query = "utm_source=fb&a=1&z=2"
pairs = [(k, v) for k, v in parse_qsl(query, keep_blank_values=False)
         if not any(k.lower().startswith(p) for p in _TRACKING_PREFIXES)]
pairs.sort()
cleaned = urlencode(pairs, doseq=True)
print(cleaned)  # a=1&z=2
assert cleaned == "a=1&z=2"
```

### Bài tập 8.3 — canonicalize_url hoàn chỉnh

**Bối cảnh:** Ghép các bước: lowercase scheme/netloc, bỏ port mặc định (:80/:443), bỏ tracking params, sort query, gộp `//` thành `/`, bỏ trailing `/`.

**Yêu cầu:** Viết `canonicalize_url(url: str) -> str` thực hiện tất cả bước trên.

Test:
```python
assert canonicalize_url("https://vnexpress.net/bai.html?utm_source=fb") == "https://vnexpress.net/bai.html"
assert canonicalize_url("HTTP://VNEXPRESS.NET:80//bai.html/") == "http://vnexpress.net/bai.html"
assert canonicalize_url("https://a.com/b?z=1&a=2") == "https://a.com/b?a=2&z=1"
```

**Đáp án:**

```python
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PREFIXES = (
    "utm_", "ga_", "yclid", "fbclid", "gclid", "mc_cid", "mc_eid",
    "vero_", "_ga", "ref", "ref_src", "ref_url", "spm", "share_source", "from", "src",
)

def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    # Bỏ port mặc định
    if (scheme == "http" and netloc.endswith(":80")) or (
        scheme == "https" and netloc.endswith(":443")
    ):
        netloc = netloc.rsplit(":", 1)[0]
    # Lọc tracking params, sort
    pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if not any(k.lower().startswith(prefix) for prefix in _TRACKING_PREFIXES)
    ]
    pairs.sort()
    # Chuẩn hóa path
    path = parts.path or "/"
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((scheme, netloc, path, urlencode(pairs, doseq=True), ""))

# Test
assert canonicalize_url("https://vnexpress.net/bai.html?utm_source=fb") == "https://vnexpress.net/bai.html"
assert canonicalize_url("HTTP://VNEXPRESS.NET:80//bai.html/") == "http://vnexpress.net/bai.html"
assert canonicalize_url("https://a.com/b?z=1&a=2") == "https://a.com/b?a=2&z=1"
print("OK!")
```

### Bài tập 8.4 — SimHash: character n-grams

**Bối cảnh:** SimHash tạo "fingerprint" 64-bit cho text. Bước đầu: tách text thành character 4-grams (cửa sổ trượt 4 ký tự).

**Yêu cầu:**
1. Viết function `_simhash_features(text: str) -> dict[str, int]`:
   - Lowercase text, extract tất cả "token" bằng regex `[\w\u4e00-\u9fcc]+`, join thành 1 chuỗi liên tục.
   - Nếu chuỗi ngắn hơn 4 ký tự → return `{chuỗi: 1}`. Nếu rỗng → return `{}`.
   - Tạo 4-grams: `joined[i:i+4]` cho `i` từ 0 đến `len - 3`.
   - Đếm số lần xuất hiện mỗi 4-gram (dùng `Counter`).
   - Cap weight tối đa 50 (tránh 1 n-gram quá dominant).
2. Test: `_simhash_features("hello")` → `{"hell": 1, "ello": 1}`.

**Đáp án:**

```python
import re
from collections import Counter

_SIMHASH_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fcc]+", re.UNICODE)
_SIMHASH_NGRAM_WIDTH = 4
_SIMHASH_WEIGHT_CAP = 50

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

# Test
features = _simhash_features("hello")
print(features)  # {'hell': 1, 'ello': 1}
assert features == {"hell": 1, "ello": 1}

features2 = _simhash_features("Hà Nội hôm nay trời nắng đẹp")
print(f"Số features: {len(features2)}")
assert len(features2) > 5
```

### Bài tập 8.5 — SimHash: hash 64-bit và Hamming distance

**Bối cảnh:** Từ features (bài 8.4), thư viện `simhash` tính hash 64-bit. 2 bài gần giống → hash có Hamming distance nhỏ (ít bit khác nhau).

**Yêu cầu:**
1. Viết `simhash64(text)`: dùng `Simhash(features, f=64)` tạo hash. Convert sang signed int 64-bit.
2. Viết `hamming(a, b)`: XOR 2 hash, đếm số bit 1 (`bin(...).count("1")`).
3. Test: 2 câu gần giống → Hamming <= 5. 2 câu khác hẳn → Hamming > 10.

**Đáp án:**

```python
from simhash import Simhash

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

# Test
h1 = simhash64("Hà Nội hôm nay trời nắng đẹp, nhiệt độ 32 độ C")
h2 = simhash64("Hà Nội hôm nay trời nắng đẹp, nhiệt độ 33 độ C")  # gần giống
h3 = simhash64("Bóng đá Việt Nam thắng Thái Lan 2-0 tại SEA Games")  # khác hẳn

d12 = hamming(h1, h2)
d13 = hamming(h1, h3)
print(f"Hamming(h1, h2) = {d12} (gần giống)")
print(f"Hamming(h1, h3) = {d13} (khác hẳn)")
assert d12 <= 5
assert d13 > 10
```

### Bài tập 8.6 — normalize_text

**Bối cảnh:** Text crawl từ web có whitespace thừa, boilerplate ("Đọc thêm:", "Tags:", "Chia sẻ"). Cần loại bỏ.

**Yêu cầu:**
1. Tạo regex `_BOILERPLATE_RE` match các dòng bắt đầu bằng "đọc thêm", "xem thêm", "tags:", "từ khóa:", "liên quan:", "chia sẻ" (case-insensitive, multiline).
2. Tạo regex `_WS_RE` match 1+ whitespace.
3. Viết `normalize_text(text)`: NFC normalize → loại bỏ boilerplate → gộp whitespace → strip.

**Đáp án:**

```python
import unicodedata

_WS_RE = re.compile(r"\s+")
_BOILERPLATE_RE = re.compile(
    r"(?im)^\s*(?:đọc thêm|doc them|xem thêm|xem them|tags?:|"
    r"từ khóa:|tu khoa:|liên quan:|lien quan:|chia sẻ|chia se).*$"
)

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = _BOILERPLATE_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()

# Test
assert normalize_text("  Tin  tức   hôm nay  ") == "Tin tức hôm nay"
assert normalize_text("Nội dung.\nĐọc thêm: bài liên quan") == "Nội dung."
assert normalize_text("Hello.\nTags: tag1, tag2") == "Hello."
assert normalize_text(None) == ""
print("OK!")
```

### Bài tập 8.7 — PoliteClient: per-host lock + delay

**Bối cảnh:** Crawler cần "lịch sự" — không gửi request quá nhanh đến cùng 1 server. Dùng asyncio Lock per host + sleep giữa các request.

**Yêu cầu:**
1. Tạo class `PoliteClient`:
   - `__init__(*, user_agent, timeout_s=20.0, crawl_delay_s=1.0, max_retries=3)`: tạo `httpx.AsyncClient`, dict `_locks` và `_last_by_host`.
   - `get(url)`: extract host từ URL → lấy Lock cho host đó → lock → tính thời gian chờ → sleep nếu cần → ghi timestamp → gọi HTTP GET.
   - Retry: dùng `AsyncRetrying` từ tenacity, retry khi status 429 hoặc 5xx.
   - `aclose()`: đóng client.
2. **Chú ý:** phần lock + delay nằm TRƯỚC retry (chỉ rate limit 1 lần), phần retry bao quanh HTTP call.

**Gợi ý cấu trúc:**
```python
async def get(self, url):
    host = urlsplit(url).netloc.lower()
    lock = self._locks.setdefault(host, asyncio.Lock())
    # Bước 1: Lock + delay
    async with lock:
        # tính wait_s, sleep nếu > 0
        self._last_by_host[host] = time.monotonic()
    # Bước 2: HTTP call với retry
    async for attempt in AsyncRetrying(...):
        with attempt:
            response = await self._client.get(url)
            if response.status_code == 429 or 500 <= response.status_code < 600:
                raise httpx.HTTPStatusError(...)
            return response
```

**Đáp án:**

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

**Yêu cầu:** Code phần đầu `app/crawler.py` (~250 dòng) gồm tất cả imports, constants, classes `PoliteClient` + `RobotsCache`, và các function helper.

**Kiểm tra:** So với `app/crawler.py` dòng 1-257 trong dự án.

---

## Chặng 9 — Crawler phần 2: Feed, Extract, Orchestration (`app/crawler.py` dòng 250-514)

**Mục tiêu:** hiểu RSS parsing, HTML extraction, crawler orchestration.

### Lý thuyết

**1. RSS parsing với feedparser:** parse XML RSS feed thành Python objects.
**2. HTML extraction:** trafilatura (chính xác) + readability + BeautifulSoup (fallback).
**3. crawl_articles:** orchestration: duyệt sources → fetch feeds → fetch articles → extract → dedupe → output.

### Bài tập 9.1 — Parse RSS entry thành ArticleCandidate

**Bối cảnh:** feedparser parse RSS XML thành dict-like objects. Mỗi entry có: `link`, `title`, `published`, `tags`, `author`.

**Yêu cầu:**
1. Cho dict giả lập RSS entry:
   ```python
   entry = {"link": "https://vnexpress.net/bai-1.html", "title": "Tin A", "published": "Mon, 01 Jan 2024 10:00:00 +0700", "tags": [{"term": "thời sự"}], "author": "NVA"}
   ```
2. Extract: `link` → `url` (canonicalize), `title` → normalize, `published` → parse datetime, `tags[0].term` → category (canonicalize), `author`.
3. Tạo `ArticleCandidate` từ các giá trị trên.

**Đáp án:**

```python
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def _to_utc(raw):
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

# Giả lập RSS entry
entry = {"link": "https://vnexpress.net/bai-1.html?utm_source=fb", "title": "  Tin A  ", "published": "Mon, 01 Jan 2024 10:00:00 +0700", "tags": [{"term": "thời sự"}], "author": "NVA"}

link = str(entry.get("link") or "")
title = normalize_text(str(entry.get("title") or ""))
published = _to_utc(entry.get("published"))
category_raw = entry["tags"][0].get("term") if entry.get("tags") else None
author = str(entry.get("author")) if entry.get("author") else None

candidate = ArticleCandidate(
    source="vnexpress", source_name="VnExpress",
    url=canonicalize_url(link), title=title,
    published_at=published,
    category=canonical_category(category_raw),
    author=author,
)
print(candidate)
assert candidate.url == "https://vnexpress.net/bai-1.html"  # utm_source bị loại
assert candidate.title == "Tin A"  # stripped
assert candidate.category == "thoi_su"
```

### Bài tập 9.2 — extract_from_html (trafilatura + fallback)

**Bối cảnh:** Sau khi fetch HTML bài báo, cần extract nội dung text. Dùng trafilatura (chính xác hơn). Nếu trafilatura không extract được → fallback: dùng `readability.Document` + `BeautifulSoup` lấy text.

**Yêu cầu:**
1. Viết `extract_from_html(html: str, *, url=None) -> ExtractedArticle | None`:
   - Nếu `html` rỗng → None.
   - Thử `trafilatura.extract(html, url=url, with_metadata=True, output_format="json", ...)`.
   - Nếu có kết quả → `json.loads`, lấy `text`, normalize, kiểm tra word_count >= 50.
   - Nếu trafilatura fail → thử `Document(html).summary()` + `BeautifulSoup(summary, "lxml").get_text(" ")`.
   - Nếu cả 2 fail → None.
2. Test: truyền HTML đơn giản, kiểm tra extract được text.

**Đáp án:**

```python
import trafilatura
from readability import Document
from bs4 import BeautifulSoup

def extract_from_html(html: str, *, url: str | None = None) -> ExtractedArticle | None:
    if not html:
        return None
    # Thử trafilatura
    try:
        extracted = trafilatura.extract(
            html, url=url, with_metadata=True, output_format="json",
            include_comments=False, include_tables=False, favor_precision=True,
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
                    content_text=text, word_count=word_count(text),
                )
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    # Fallback: readability + BeautifulSoup
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

**Yêu cầu:** Ghép chặng 8 + 9 thành file `app/crawler.py` (514 dòng) hoàn chỉnh:
- Tất cả từ chặng 8 (imports, constants, PoliteClient, RobotsCache, helpers)
- `fetch_feed`, `extract_from_html` từ chặng 9
- `crawl_articles` async function (orchestration)
- `write_jsonl`, `_validate_cli_output_path`, `_build_parser`, `_run_cli`, `main`

**Kiểm tra:** So với `app/crawler.py` trong dự án — phải giống 100%.

---

## Chặng 10 — ViT5 Summarizer (`app/summarizer.py`)

**Mục tiêu:** hiểu lazy loading, PEFT adapter, tokenizer, batch inference. Code lại `app/summarizer.py`.

### Lý thuyết

**1. Lazy loading:** model nặng, chỉ load khi cần (`_ensure_loaded`).
**2. PEFT adapter:** LoRA adapter nhỏ (~vài MB) + base model lớn.
**3. Batch inference:** xử lý nhiều bài cùng lúc cho nhanh.

### Bài tập 10.1 — GenerationConfig dataclass

**Bối cảnh:** Config cho model inference: max input length, max output tokens, beam search params, batch size.

**Yêu cầu:** Tạo `GenerationConfig` dataclass (slots=True) với 7 fields và default values:
- `max_input_length: int = 1024` — cắt input dài hơn 1024 token
- `max_new_tokens: int = 128` — summary tối đa 128 token
- `num_beams: int = 4` — beam search (nhiều beam → chất lượng hơn, chậm hơn)
- `no_repeat_ngram_size: int = 3` — tránh lặp 3-gram
- `length_penalty: float = 1.0` — penalty cho output dài
- `early_stopping: bool = True` — dừng sớm khi đủ beam kết thúc
- `batch_size: int = 4` — xử lý 4 bài/batch

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

cfg = GenerationConfig()
print(cfg)
assert cfg.max_input_length == 1024
assert cfg.batch_size == 4
```

### Bài tập 10.2 — Lazy loading pattern

**Bối cảnh:** Model AI nặng hàng GB. Không nên load ngay khi tạo `ViT5Summarizer()` (chậm, tốn RAM). Thay vào đó, load lần đầu gọi `summarize()`.

**Yêu cầu:**
1. Viết class đơn giản `LazyModel`:
   - `__init__`: `self._model = None`, `self.model_name = "vit5-base"`.
   - `_ensure_loaded()`: nếu `_model` is None → print "Loading..." → set `_model = {"name": self.model_name}` (giả lập).
   - `predict(text)`: gọi `_ensure_loaded()`, dùng `_model`.
2. Test: tạo `LazyModel()` → chưa print "Loading". Gọi `predict("x")` → print "Loading" lần đầu. Gọi lần 2 → không print lại.

**Đáp án:**

```python
class LazyModel:
    def __init__(self, model_name="vit5-base"):
        self.model_name = model_name
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return self._model
        print(f"Loading model {self.model_name}...")
        self._model = {"name": self.model_name, "loaded": True}
        return self._model

    def predict(self, text):
        model = self._ensure_loaded()
        return f"[{model['name']}] prediction for: {text[:20]}"

# Test
m = LazyModel()
print("Vừa tạo, chưa load.")
result1 = m.predict("Bài báo dài...")  # In "Loading model..."
result2 = m.predict("Bài khác...")     # Không in lại
print(result1)
print(result2)
```

### Bài tập 10.3 — Empty mask + batch processing

**Bối cảnh:** `summarize_batch(texts)` nhận list texts, một số có thể rỗng. Cần:
1. Tạo `empty_mask` đánh dấu text nào rỗng.
2. Chỉ tokenize + generate cho text non-empty.
3. Re-insert `""` cho các vị trí rỗng.

**Yêu cầu:**
1. Cho `texts = ["Bài 1 dài...", "", "Bài 3 dài...", "  ", "Bài 5"]`.
2. Tạo `empty_mask`: `[False, True, False, True, False]`.
3. Filter `non_empty`: `["Bài 1 dài...", "Bài 3 dài...", "Bài 5"]`.
4. Giả sử generate trả `["Sum1", "Sum3", "Sum5"]`.
5. Re-insert: `["Sum1", "", "Sum3", "", "Sum5"]`.

**Đáp án:**

```python
texts = ["Bài 1 dài...", "", "Bài 3 dài...", "  ", "Bài 5"]

# Bước 1: empty mask
empty_mask = [not text or not text.strip() for text in texts]
print(f"empty_mask: {empty_mask}")  # [False, True, False, True, False]

# Bước 2: filter non-empty
non_empty = [text for text, is_empty in zip(texts, empty_mask) if not is_empty]
print(f"non_empty: {non_empty}")  # ['Bài 1 dài...', 'Bài 3 dài...', 'Bài 5']

# Bước 3: giả lập generate
decoded = [f"Summary of {t[:10]}" for t in non_empty]
print(f"decoded: {decoded}")

# Bước 4: re-insert
result = []
cursor = 0
for is_empty in empty_mask:
    if is_empty:
        result.append("")
    else:
        result.append(decoded[cursor])
        cursor += 1

print(f"result: {result}")
assert result[1] == ""  # vị trí rỗng
assert result[3] == ""  # vị trí rỗng
assert len(result) == len(texts)
```

### 🎯 Bài cuối chặng 10 — Code lại `app/summarizer.py`

**Yêu cầu:** Tạo file `app/summarizer.py` (138 dòng):
- `GenerationConfig` dataclass (7 fields)
- `ViT5Summarizer` class:
  - `__init__` (model_id, base_model_id, token, device, generation) — đọc env vars
  - `_load_as_peft_adapter(transformers)` → `tuple | None` — thử load PEFT, nếu fail trả None
  - `_ensure_loaded()` → `(model, tokenizer)` — lazy load
  - `summarize(text)` → str — wrap `summarize_batch`
  - `summarize_batch(texts)` → list[str] — empty mask, batch generate, re-insert

**Kiểm tra:** So với `app/summarizer.py` trong dự án — phải giống 100%.

---

## Chặng 11 — FastAPI Web Demo (`app/main.py` + `app/templates/index.html`)

**Mục tiêu:** hiểu FastAPI routes, Jinja2 templates, fetch API, XSS prevention. Code lại cả 2 file.

### Lý thuyết

**1. FastAPI:** framework web nhanh, type-safe, auto-generate API docs.
**2. Jinja2 templates:** render HTML với biến Python.
**3. XSS prevention:** escape HTML trước khi chèn vào DOM.

### Bài tập 11.1 — FastAPI Hello World

**Bối cảnh:** Bước đầu: tạo app FastAPI đơn giản với 1 GET route.

**Yêu cầu:**
1. Tạo `app = FastAPI(title="test")`.
2. Route `GET /healthz` trả `{"status": "ok"}`.
3. (Không cần chạy server, chỉ viết code.)

**Đáp án:**

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="test")

class HealthResponse(BaseModel):
    status: str

@app.get("/healthz", response_model=HealthResponse)
async def healthz():
    return HealthResponse(status="ok")
```

### Bài tập 11.2 — Jinja2 template rendering

**Bối cảnh:** FastAPI dùng Jinja2 render HTML. Template có placeholder `{{ variable }}`.

**Yêu cầu:**
1. Tạo `templates = Jinja2Templates(directory="app/templates")`.
2. Route `GET /` trả HTML render từ template `index.html`, truyền biến `model_id` và `max_articles`.

**Đáp án:**

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,  # bắt buộc phải có
        "model_id": "VietAI/vit5-base",
        "max_articles": 5,
    })
```

### Bài tập 11.3 — POST endpoint: crawl + summarize

**Bối cảnh:** Endpoint chính: crawl bài mới → summarize → trả JSON.

**Yêu cầu:**
1. Route `POST /api/summarize-today` → `SummarizeResponse`.
2. Gọi `crawl_articles(mode="demo", limit=limit)`.
3. Nếu không có bài → `HTTPException(502)`.
4. Gọi `summarizer.summarize_batch(...)`.
5. Nếu model lỗi → `HTTPException(500)`.
6. Trả `SummarizeResponse` với date, total, items.

**Đáp án:**

```python
import os
from datetime import date
from fastapi import HTTPException
from app.crawler import crawl_articles
from app.schemas import SummarizeResponse, SummaryItem
from app.summarizer import ViT5Summarizer

summarizer = ViT5Summarizer()

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

### Bài tập 11.4 — escapeHtml (JavaScript XSS prevention)

**Bối cảnh:** Dữ liệu từ server (title, summary) có thể chứa HTML/script độc hại. Trước khi chèn vào DOM bằng `innerHTML`, phải escape.

**Yêu cầu:**
1. Viết function JavaScript `escapeHtml(value)`:
   - Thay `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#039;`.
2. Test: `escapeHtml('<script>alert("xss")</script>')` → safe string.

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

// Test (trong browser console):
// escapeHtml('<script>alert("xss")</script>')
// → '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
```

### 🎯 Bài cuối chặng 11 — Code lại `app/main.py` + `app/templates/index.html`

**Yêu cầu:**
1. `app/main.py` (66 dòng): 3 routes, global summarizer, APP_VERSION = "0.2.0-simple".
2. `app/templates/index.html` (140 dòng): HTML + CSS + JavaScript:
   - CSS variables (--bg, --panel, --text, --muted, --line, --accent, --accent-dark)
   - Responsive layout
   - `escapeHtml` function
   - `fetch("/api/summarize-today")` + render results
   - Jinja2: `{{ model_id }}`, `{{ max_articles }}`

**Kiểm tra:** So với `app/main.py` và `app/templates/index.html` trong dự án — phải giống 100%.

---

## Tổng Kết — Thứ Tự Code Lại Dự Án Hoàn Chỉnh

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
| 9 | `labeling/batch_labeler.py` | 6B |
| 10 | `labeling/split_dataset.py` | 7 |
| 11 | `app/crawler.py` | 8+9 |
| 12 | `app/summarizer.py` | 10 |
| 13 | `app/main.py` | 11 |
| 14 | `app/templates/index.html` | 11 |
| 15 | `requirements.txt` | copy |
| 16 | `pyproject.toml` | copy |
| 17 | `.env.example` | copy |
| 18 | `Makefile` | copy |
| 19 | `README.md` | copy |
| 20 | `Dockerfile` + `docker-compose.yml` | copy |

**Tiêu chí hoàn thành:** Chạy được:
```bash
python -m app.crawler --mode labeling --source vnexpress --limit 5 --output data/raw/test.jsonl
python -m labeling.label_dataset --input data/raw/test.jsonl --output data/labeled/test.jsonl --limit 3
python -m labeling.batch_labeler --input data/raw/test.jsonl --output data/labeled/batch_test.jsonl --limit 5
python -m labeling.split_dataset --input data/labeled/test.jsonl --output data/datasets/test
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
| 5 | 6B-7 | Batch labeling (rate limit, key rotation) + Split dataset |
| 6 | 8-9 | Crawler (URL, SimHash, HTTP, RSS, extract) |
| 7 | 10 | ViT5 Summarizer (PEFT, tokenizer, batch) |
| 8 | 11 | FastAPI + HTML + tổng kết code lại dự án |
