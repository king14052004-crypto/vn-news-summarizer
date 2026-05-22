# Lộ Trình Học Để Tự Code Lại `vn-news-summarizer`

Tài liệu này dành cho người mới học, chưa cần biết trước cấu trúc dự án. Mục tiêu không phải là học thuộc code hiện có, mà là hiểu từng mảnh nhỏ rồi tự code lại được toàn bộ pipeline: crawl tin tức, tạo nhãn bằng Gemini (AI Studio), kiểm tra chất lượng dữ liệu, chia dataset, fine-tune ViT5 + LoRA, load model để inference, và chạy web demo bằng FastAPI.

Dự án sau khi đơn giản hóa có các phần chính:

```text
vn-news-summarizer/
├── app/                         # Web demo, crawler, inference model
│   ├── main.py                  # FastAPI routes
│   ├── crawler.py               # Crawl RSS, extract article text, write JSONL
│   ├── schemas.py               # Kiểu dữ liệu dùng chung
│   ├── sources.py               # Cấu hình nguồn báo
│   ├── summarizer.py            # Load ViT5/LoRA và summarize
│   └── templates/index.html     # Giao diện bấm nút tóm tắt
├── labeling/                    # Pipeline tạo nhãn và dataset
│   ├── prompt.py                # Prompt, parser JSON output từ Gemini
│   ├── gemini_labeler.py        # Gọi AI Studio Gemini (free key, xoay vòng)
│   ├── vertex_labeler.py        # Gọi Vertex AI Gemini (legacy, trả phí)
│   ├── label_dataset.py         # Đọc bài raw, gọi labeler, ghi JSONL
│   ├── qc.py                    # Kiểm tra chất lượng summary
│   └── split_dataset.py         # Chia train/val/test
├── notebooks/finetune_vit5_lora.ipynb
├── data/                        # Dữ liệu local, thường bị .gitignore
├── docs/                        # Report và tài liệu học
├── Dockerfile
└── docker-compose.yml
```

## Cách Học Để Không Bị Ngợp

1. Mỗi chặng chỉ học đúng một nhóm kiến thức.
2. Làm bài tập nhỏ trước, không mở code dự án để copy.
3. Sau khi làm được bài nhỏ, mới mở file dự án để so sánh ý tưởng.
4. Cuối mỗi chặng có một bài "code lại phần dự án" với yêu cầu cụ thể.
5. Nếu mắc lỗi, ghi lại lỗi, command đã chạy, input đã dùng, output mong đợi.
6. Chỉ sang chặng tiếp theo khi checklist cuối chặng đã đạt.

Quy ước trong tài liệu:

- **Bài tập nhỏ:** dùng dữ liệu giả, mục tiêu là hiểu kỹ thuật.
- **Đáp án/kết quả đúng:** không nhất thiết là code duy nhất, nhưng output phải giống.
- **Bài cuối chặng:** mô phỏng lại function/file thật trong dự án, mô tả như thể bạn chưa đọc repo.
- **Không copy:** bạn có thể nhìn lại đáp án sau khi tự thử ít nhất 20-30 phút.
- **So sánh dự án:** sau mỗi bài cuối chặng, mở file tương ứng trong dự án để so sánh cách tiếp cận.

---

## Chặng 0 - Nền Tảng Python Cho Dự Án

**Mục tiêu:** hiểu cách một project Python được chia thành nhiều file, biết đọc/ghi dữ liệu JSONL, biết chạy file bằng command line, hiểu biến môi trường.

### Bạn cần hiểu gì?

- `module` là một file Python, ví dụ `crawler.py`.
- `package` là một thư mục có `__init__.py`, ví dụ `app/`, `labeling/`.
- `import` giúp dùng code từ file khác. Ví dụ: `from app.schemas import CrawledArticle`.
- `python -m app.crawler` nghĩa là chạy module `crawler.py` nằm trong package `app`.
- JSON là một object/list dữ liệu.
- JSONL là nhiều dòng JSON, mỗi dòng là một record riêng. Dự án dùng JSONL thay database vì đơn giản, dễ append, dễ debug.
- `Path` (từ `pathlib`) giúp code chạy ổn hơn trên Windows/Linux vì tự xử lý `/` và `\`.
- `argparse` giúp tạo command có tham số như `--input`, `--output`, `--limit`.
- **Biến môi trường (env var)** là cách truyền cấu hình cho chương trình mà không sửa code:
  - Đặt trong file `.env` hoặc `export KEY=value` trong terminal.
  - Đọc bằng `os.environ.get("KEY", "default_value")`.
  - Dự án dùng `.env.example` làm mẫu; copy thành `.env` rồi điền giá trị thật.

### File/function trong dự án liên quan

- `app/__init__.py`, `labeling/__init__.py`: file rỗng hoặc chứa docstring, đánh dấu thư mục là package.
- `app/schemas.py`: định nghĩa object dữ liệu dùng giữa crawler, API, summarizer.
- `labeling/split_dataset.py`: có helper `read_jsonl()`, `write_jsonl()`, CLI.
- `app/crawler.py`: có `_build_parser()`, `_run_cli()`, `main()` để chạy crawler bằng command.
- `.env.example`: mẫu cấu hình dự án.

### Bài tập nhỏ 0.1 - Viết và đọc file text

**Yêu cầu:** tạo file `practice_file.py` có 2 function:

- `write_text(path, text)`: ghi chuỗi vào file.
- `read_text(path)`: đọc lại chuỗi từ file.

Chạy thử:

```bash
python practice_file.py
```

**Đáp án gợi ý:**

```python
from pathlib import Path

def write_text(path, text):
    Path(path).write_text(text, encoding="utf-8")

def read_text(path):
    return Path(path).read_text(encoding="utf-8")

write_text("hello.txt", "Xin chao")
print(read_text("hello.txt"))
```

**Kết quả đúng:** terminal in ra `Xin chao`, thư mục có file `hello.txt`.

### Bài tập nhỏ 0.2 - JSON khác JSONL

**Yêu cầu:** tạo 3 học sinh:

```python
students = [
    {"id": 1, "name": "An", "score": 8.5},
    {"id": 2, "name": "Binh", "score": 7.0},
    {"id": 3, "name": "Chi", "score": 9.0},
]
```

Ghi ra 2 file:

- `students.json`: một list JSON lớn.
- `students.jsonl`: mỗi học sinh là một dòng JSON.

**Đáp án gợi ý:**

```python
import json
from pathlib import Path

Path("students.json").write_text(
    json.dumps(students, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

with Path("students.jsonl").open("w", encoding="utf-8") as f:
    for row in students:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
```

**Kết quả đúng:**

- `students.json` nhìn giống một list có dấu `[` và `]`.
- `students.jsonl` có đúng 3 dòng.
- Mỗi dòng trong `students.jsonl` tự parse được bằng `json.loads()`.

### Bài tập nhỏ 0.3 - Tạo CLI đơn giản

**Yêu cầu:** tạo file `practice_cli.py`, chạy được:

```bash
python practice_cli.py --name An --repeat 3
```

Output mong muốn:

```text
Hello An
Hello An
Hello An
```

**Đáp án gợi ý:**

```python
import argparse

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--repeat", type=int, default=1)
    return parser

def main():
    args = build_parser().parse_args()
    for _ in range(args.repeat):
        print(f"Hello {args.name}")

if __name__ == "__main__":
    main()
```

### Bài tập nhỏ 0.4 - Đọc biến môi trường

**Yêu cầu:** tạo file `practice_env.py`:

- Đọc biến `MY_NAME` từ môi trường. Nếu không có, dùng `"World"`.
- In ra `Hello <MY_NAME>`.

**Đáp án gợi ý:**

```python
import os

name = os.environ.get("MY_NAME", "World")
print(f"Hello {name}")
```

**Command tự kiểm tra:**

```bash
python practice_env.py           # In: Hello World
MY_NAME=An python practice_env.py  # In: Hello An
```

**Liên hệ dự án:** mở file `.env.example` trong dự án, bạn sẽ thấy các biến như `HF_MODEL_ID`, `GEMINI_API_KEYS`, `MAX_ARTICLES_PER_DEMO`. Tất cả đều được đọc bằng `os.environ.get(...)` trong code.

### Bài tập nhỏ 0.5 - Hiểu `__init__.py` và package import

**Yêu cầu:** tạo cấu trúc:

```text
mypackage/
├── __init__.py   (nội dung: rỗng hoặc chỉ có docstring)
└── utils.py      (nội dung: hàm greet(name))
```

Viết `test_import.py` ở bên ngoài `mypackage/`:

```python
from mypackage.utils import greet
print(greet("An"))
```

**Đáp án gợi ý:**

`mypackage/__init__.py`:

```python
"""My practice package."""
```

`mypackage/utils.py`:

```python
def greet(name):
    return f"Hello {name}"
```

**Kết quả đúng:** `python test_import.py` in ra `Hello An`.

**Liên hệ dự án:** dự án có `app/__init__.py` và `labeling/__init__.py` để Python hiểu đây là package. Khi chạy `python -m app.crawler`, Python tìm `app/crawler.py` nhờ `__init__.py` đánh dấu `app/` là package.

### Bài cuối chặng 0 - Code lại helper JSONL cho dự án

**Bối cảnh:** dự án cần lưu bài báo, nhãn, dataset bằng JSONL vì dễ đọc, dễ append, không cần database.

**File tự tạo:** `practice_jsonl.py`.

**Yêu cầu cụ thể:**

1. Viết `write_jsonl(path, rows)`:
   - `path` có thể là string hoặc `Path`.
   - `rows` là list dict.
   - Tự tạo thư mục cha nếu chưa tồn tại (`Path(path).parent.mkdir(parents=True, exist_ok=True)`).
   - Ghi mỗi dict thành 1 dòng JSON.
   - Dùng `ensure_ascii=False` để giữ tiếng Việt.
2. Viết `read_jsonl(path)`:
   - Trả về list dict.
   - Bỏ qua dòng trống.
   - Nếu file không tồn tại thì trả list rỗng.
3. Trong `main`, tạo 3 record học sinh, ghi `data/practice/students.jsonl`, đọc lại và in số dòng.

**Code khung:**

```python
from pathlib import Path
import json

def write_jsonl(path, rows):
    # TODO
    pass

def read_jsonl(path):
    # TODO
    pass

def main():
    rows = [
        {"id": 1, "name": "An", "score": 8.5},
        {"id": 2, "name": "Binh", "score": 7.0},
        {"id": 3, "name": "Chi", "score": 9.0},
    ]
    write_jsonl("data/practice/students.jsonl", rows)
    loaded = read_jsonl("data/practice/students.jsonl")
    print(len(loaded))

if __name__ == "__main__":
    main()
```

**Đáp án gợi ý:**

```python
from pathlib import Path
import json

def write_jsonl(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def read_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def main():
    rows = [
        {"id": 1, "name": "An", "score": 8.5},
        {"id": 2, "name": "Binh", "score": 7.0},
        {"id": 3, "name": "Chi", "score": 9.0},
    ]
    write_jsonl("data/practice/students.jsonl", rows)
    loaded = read_jsonl("data/practice/students.jsonl")
    print(len(loaded))

if __name__ == "__main__":
    main()
```

**Kết quả đúng:**

```bash
python practice_jsonl.py
# 3
```

**So sánh dự án:** mở `labeling/split_dataset.py` dòng 25-39 và `labeling/label_dataset.py` dòng 24-39 để thấy `read_jsonl()` và `write_jsonl()` tương tự.

Checklist qua chặng:

- Bạn giải thích được JSONL là gì và vì sao dataset dùng JSONL thay vì database.
- Bạn hiểu `__init__.py` dùng để làm gì.
- Bạn tự viết được `read_jsonl()` và `write_jsonl()`.
- Bạn biết đọc biến môi trường bằng `os.environ.get()`.
- Bạn chạy được file bằng `python file.py` và `python -m package.module`.

---

## Chặng 1 - Data Schema Và Source Config

**Mục tiêu:** hiểu dữ liệu đi qua pipeline có hình dạng gì và vì sao cần cấu hình nguồn báo rõ ràng.

### Bạn cần hiểu gì?

- Nếu truyền dict lung tung, rất dễ sai key như `content`, `content_text`, `article_text`.
- `dataclass` giúp gom dữ liệu thành object rõ field, Python tự tạo `__init__`, `__repr__`.
- `@dataclass(slots=True)` tiết kiệm bộ nhớ hơn.
- `frozen=True` làm object khó bị sửa nhầm sau khi tạo (immutable).
- `str | None` nghĩa là field có thể là chuỗi hoặc không có giá trị.
- **Pydantic `BaseModel`** khác `dataclass`:
  - Pydantic validate dữ liệu khi tạo object (ví dụ: `confidence` phải >= 0.0, <= 1.0).
  - Pydantic có `.model_dump()` để chuyển thành dict.
  - FastAPI dùng Pydantic để validate request/response.
- Source config giúp crawler biết báo nào enabled, RSS URL nào cần đọc, domain nào hợp lệ.

### File/function trong dự án

- `app/schemas.py`
  - `ArticleCandidate`: bài báo mới lấy từ RSS, chưa fetch HTML. Có `source`, `source_name`, `url`, `title`, `published_at`, `category`, `author`.
  - `CrawledArticle`: bài báo đã có `content_text`. Có thêm `article_id`, `word_count`, `url_hash`. Có method `to_jsonl_record()`.
  - `SummaryItem`: response item trả về web/API (Pydantic).
  - `SummarizeResponse`, `HealthResponse`: Pydantic response models cho FastAPI.
- `app/sources.py`
  - `USER_AGENT`: chuỗi User-Agent cho HTTP request.
  - `CRAWL_DELAY_SECONDS`, `TIMEOUT_SECONDS`, `MAX_RETRIES`: hằng số cấu hình.
  - `NewsSource`: dataclass cấu hình một nguồn tin (id, name, domain, rss, enabled, max_items_per_feed).
  - `SOURCES`: danh sách nguồn chuẩn (VnExpress, Tuoi Tre, Thanh Nien, VietnamNet, Dan Tri, Znews, VTC News, Lao Dong).
  - `CANONICAL_CATEGORIES`: dict map category thô sang category chuẩn.
  - `enabled_sources(only)`: lọc nguồn đang bật.
  - `canonical_category(raw)`: chuẩn hóa category.

### Bài tập nhỏ 1.1 - Dataclass đầu tiên

**Yêu cầu:** tạo `practice_dataclass.py`, định nghĩa `Student` có:

- `id: str`
- `name: str`
- `score: float`
- `email: str | None = None`

Tạo một student và in ra `name`.

**Đáp án gợi ý:**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Student:
    id: str
    name: str
    score: float
    email: str | None = None

student = Student(id="s1", name="An", score=8.5)
print(student.name)
```

**Kết quả đúng:** in ra `An`.

### Bài tập nhỏ 1.2 - Pydantic response model

**Yêu cầu:** tạo model `StudentResponse` bằng `pydantic.BaseModel` có `id`, `name`, `passed`. Tạo object và gọi `.model_dump()`.

**Đáp án gợi ý:**

```python
from pydantic import BaseModel

class StudentResponse(BaseModel):
    id: str
    name: str
    passed: bool

response = StudentResponse(id="s1", name="An", passed=True)
print(response.model_dump())
```

**Kết quả đúng:** output là dict `{"id": "s1", "name": "An", "passed": True}`.

### Bài tập nhỏ 1.3 - Pydantic với Field validation

**Yêu cầu:** tạo `ScoreItem` có:

- `name: str`
- `score: float` phải >= 0 và <= 10 (dùng `Field(ge=0, le=10)`)
- `tags: list[str]` mặc định rỗng (dùng `Field(default_factory=list)`)

Thử tạo object với `score=15` và quan sát lỗi.

**Đáp án gợi ý:**

```python
from pydantic import BaseModel, Field, ValidationError

class ScoreItem(BaseModel):
    name: str
    score: float = Field(ge=0, le=10)
    tags: list[str] = Field(default_factory=list)

good = ScoreItem(name="An", score=8.5)
print(good.model_dump())

try:
    bad = ScoreItem(name="Binh", score=15)
except ValidationError as e:
    print("Validation error:", e.error_count(), "errors")
```

**Kết quả đúng:** object `good` tạo thành công; `bad` raise `ValidationError`.

**Liên hệ dự án:** mở `labeling/prompt.py` dòng 61-65, class `LabelOutput` dùng `Field(default=0.0, ge=0.0, le=1.0)` cho `confidence`. Mở `app/schemas.py` dòng 56-58, `SummarizeResponse` dùng `Field(ge=0)` cho `total`.

### Bài tập nhỏ 1.4 - Source config đơn giản

**Yêu cầu:** tạo `BookSource`:

```python
@dataclass(frozen=True)
class BookSource:
    id: str
    name: str
    urls: tuple[str, ...]
    enabled: bool = True
```

Tạo 4 source, trong đó 1 source `enabled=False`. Viết `enabled_sources(only=None)`.

**Đáp án gợi ý:**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BookSource:
    id: str
    name: str
    urls: tuple[str, ...]
    enabled: bool = True

SOURCES = [
    BookSource(id="a", name="Alpha", urls=("http://a.com/1",)),
    BookSource(id="b", name="Beta", urls=("http://b.com/1",)),
    BookSource(id="c", name="Gamma", urls=("http://c.com/1",), enabled=False),
    BookSource(id="d", name="Delta", urls=("http://d.com/1",)),
]

def enabled_sources(only=None):
    selected = []
    only_set = set(only) if only else None
    for source in SOURCES:
        if not source.enabled:
            continue
        if only_set is not None and source.id not in only_set:
            continue
        selected.append(source)
    return selected
```

**Kết quả đúng:**

```python
assert len(enabled_sources()) == 3
assert enabled_sources({"missing"}) == []
```

### Bài tập nhỏ 1.5 - Chuẩn hóa category

**Yêu cầu:** viết `normalize_category(raw)`:

- `"sci-fi"` và `"science fiction"` thành `"fiction"`.
- `"biz"` và `"business"` thành `"business"`.
- `None` trả `None`.
- Text lạ thì lowercase và strip.

**Đáp án gợi ý:**

```python
CATEGORY_MAP = {
    "sci-fi": "fiction",
    "science fiction": "fiction",
    "biz": "business",
    "business": "business",
}

def normalize_category(raw):
    if raw is None:
        return None
    key = raw.strip().lower()
    return CATEGORY_MAP.get(key, key or None)
```

**Liên hệ dự án:** mở `app/sources.py` dòng 154-189. Dự án dùng `CANONICAL_CATEGORIES` dict với logic phức tạp hơn: kiểm tra alias chứa trong needle hoặc needle chứa trong alias. Bạn sẽ thấy pattern tương tự.

### Bài tập nhỏ 1.6 - Method `to_dict()` trên dataclass

**Yêu cầu:** thêm method `to_dict()` cho `Student` dataclass, trả dict chỉ chứa field có giá trị (bỏ field `None`).

**Đáp án gợi ý:**

```python
from dataclasses import dataclass, fields

@dataclass(frozen=True)
class Student:
    id: str
    name: str
    score: float
    email: str | None = None

    def to_dict(self):
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}

student = Student(id="s1", name="An", score=8.5)
print(student.to_dict())
# {"id": "s1", "name": "An", "score": 8.5}
```

**Liên hệ dự án:** mở `app/schemas.py` dòng 36-45, `CrawledArticle.to_jsonl_record()` chọn các field cần cho JSONL output.

### Bài cuối chặng 1 - Code lại schema và source config kiểu dự án

**Bối cảnh:** crawler cần 2 kiểu dữ liệu:

- Bài mới lấy từ RSS: có title, url, source, category, published date.
- Bài đã extract: có thêm `content_text`, `article_id`, `word_count`.

**File tự tạo:** `practice_project_schema.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `ArticleCandidate` (frozen, slots):
   - `source: str`
   - `source_name: str`
   - `title: str`
   - `url: str`
   - `category: str | None = None`
   - `published_at: str | None = None`
2. Tạo dataclass `CrawledArticle` (frozen, slots):
   - `article_id: int`
   - `source: str`
   - `source_name: str`
   - `url: str`
   - `title: str`
   - `content_text: str`
   - `category: str | None = None`
   - `published_at: str | None = None`
   - `word_count: int = 0`
   - `url_hash: str = ""`
   - Method `to_jsonl_record()` trả dict gồm: `article_id`, `source`, `url`, `title`, `category`, `published_at`, `content_text`.
3. Tạo Pydantic `SummaryItem` có: `title`, `source`, `url`, `published_at: str | None`, `summary`.
4. Tạo dataclass `NewsSource` (frozen, slots): `id`, `name`, `domain`, `rss: list[str]`, `enabled: bool = True`, `max_items_per_feed: int | None = None`.
5. Tạo 3 nguồn fake, trong đó 1 nguồn disabled.
6. Viết `enabled_sources(only=None)`.
7. Viết `canonical_category(raw)` dùng dict alias.

**Tự kiểm tra:**

```python
sources = enabled_sources()
assert len(sources) == 2
candidate = ArticleCandidate(source="demo", source_name="Demo", title="Tin A", url="https://example.com/a")
assert candidate.title == "Tin A"
article = CrawledArticle(article_id=1, source="demo", source_name="Demo", url="https://example.com/a", title="Tin A", content_text="Nội dung bài viết dài.")
record = article.to_jsonl_record()
assert "content_text" in record
assert "word_count" not in record  # to_jsonl_record không chứa word_count
```

**So sánh dự án:** mở `app/schemas.py` và `app/sources.py` để so code.

Checklist qua chặng:

- Bạn hiểu khác nhau giữa dataclass và Pydantic model.
- Bạn biết khi nào dùng `frozen=True`.
- Bạn biết một article đi từ RSS sang extracted article như thế nào.
- Bạn tự code được cấu hình source không phụ thuộc database.

---

## Chặng 2 - HTTP, RSS, Async Và CLI Crawler Tối Giản

**Mục tiêu:** đọc được RSS feed, lấy ra danh sách bài báo gồm title và URL, hiểu async cơ bản.

### Bạn cần hiểu gì?

- HTTP request là gửi yêu cầu tới URL và nhận response (status code, body).
- RSS là XML, thường có nhiều item, mỗi item có `title`, `link`, `published`.
- `httpx.AsyncClient` giúp gọi HTTP async (không chặn chương trình).
- **async/await cơ bản:**
  - `async def f():` tạo coroutine.
  - `await some_coroutine()` chờ kết quả.
  - `asyncio.run(main())` chạy event loop.
  - Nhiều coroutine có thể chạy song song bằng `asyncio.gather()`.
- `feedparser.parse()` biến XML RSS thành object Python dễ đọc.
- CLI giúp chạy crawler bằng command thay vì sửa code.
- **Ngày tháng (datetime):**
  - RSS feed thường chứa ngày dạng RFC 2822: `"Thu, 22 May 2025 10:30:00 +0700"`.
  - `email.utils.parsedate_to_datetime()` parse được format này.
  - Cần chuẩn hóa về UTC để dễ so sánh.

### File/function trong dự án

- `app/crawler.py`
  - `PoliteClient`: client HTTP có timeout/rate limit/retry.
  - `fetch_feed()`: lấy RSS và parse ra `ArticleCandidate`.
  - `_to_utc()`: chuẩn hóa ngày tháng từ RSS sang UTC string.
  - `_category_from_url()`: đoán category từ RSS URL hoặc article URL.

### Bài tập nhỏ 2.1 - Request một URL

**Yêu cầu:** tạo `practice_http.py`, dùng `httpx` request một URL và in status code.

**Đáp án gợi ý:**

```python
import httpx

response = httpx.get("https://example.com", timeout=10)
print(response.status_code)
print(response.text[:80])
```

**Kết quả đúng:** status code thường là `200`, text bắt đầu bằng HTML.

### Bài tập nhỏ 2.2 - Async request

**Yêu cầu:** viết async function `fetch_text(url)` trả về text HTML.

**Đáp án gợi ý:**

```python
import asyncio
import httpx

async def fetch_text(url):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

async def main():
    text = await fetch_text("https://example.com")
    print(len(text))

asyncio.run(main())
```

### Bài tập nhỏ 2.3 - Parse RSS

**Yêu cầu:** tạo `practice_rss_parse.py`, dùng `feedparser` parse XML RSS thật và in 5 title đầu.

**Đáp án gợi ý:**

```python
import httpx
import feedparser

response = httpx.get("https://vnexpress.net/rss/thoi-su.rss", timeout=15)
feed = feedparser.parse(response.text)
print(f"Feed title: {feed.feed.get('title', 'N/A')}")
print(f"Total entries: {len(feed.entries)}")
for entry in feed.entries[:5]:
    print(f"  - {entry.get('title')} | {entry.get('link')}")
```

**Kết quả đúng:** mỗi dòng có title và link bài viết từ VnExpress.

### Bài tập nhỏ 2.4 - Parse ngày từ RSS

**Yêu cầu:** viết `parse_rss_date(date_string)` parse ngày từ RSS entry. Nếu lỗi trả `None`.

**Đáp án gợi ý:**

```python
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

def parse_rss_date(date_string):
    if not date_string:
        return None
    try:
        dt = parsedate_to_datetime(date_string)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None

# Test
print(parse_rss_date("Thu, 22 May 2025 10:30:00 +0700"))
# 2025-05-22T03:30:00+00:00
print(parse_rss_date("invalid"))
# None
```

**Liên hệ dự án:** mở `app/crawler.py`, tìm hàm `_to_utc()`. Logic tương tự nhưng dự án xử lý thêm một số edge case.

### Bài tập nhỏ 2.5 - asyncio.gather chạy song song

**Yêu cầu:** dùng `asyncio.gather()` fetch 3 URL cùng lúc và in thời gian.

**Đáp án gợi ý:**

```python
import asyncio
import time
import httpx

async def fetch_status(url):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        return url, r.status_code

async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/get",
        "https://httpbin.org/status/200",
    ]
    start = time.monotonic()
    results = await asyncio.gather(*[fetch_status(u) for u in urls])
    elapsed = time.monotonic() - start
    for url, status in results:
        print(f"{status} {url}")
    print(f"Total time: {elapsed:.2f}s (parallel, not 3x sequential)")

asyncio.run(main())
```

**Kết quả đúng:** tổng thời gian gần bằng 1 request đơn (vì chạy song song).

### Bài tập nhỏ 2.6 - CLI nhận URL RSS

**Yêu cầu:** chạy được:

```bash
python practice_rss.py --url https://vnexpress.net/rss/thoi-su.rss --limit 5
```

Output: 5 dòng, mỗi dòng là title.

**Gợi ý xử lý lỗi:** nếu request lỗi, return list rỗng và in message ngắn như `fetch failed: ...`.

### Bài cuối chặng 2 - Code lại RSS discovery tối giản

**Bối cảnh:** trước khi crawl nội dung, dự án phải đọc RSS để biết có những URL bài báo nào.

**File tự tạo:** `practice_rss_crawler.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `ArticleCandidate` gồm `source`, `source_name`, `title`, `url`, `category`, `published_at`.
2. Viết async function `fetch_feed(source_id, source_name, rss_url, limit)`:
   - Request RSS bằng `httpx.AsyncClient`.
   - Parse bằng `feedparser`.
   - Trả list `ArticleCandidate`.
   - Nếu feed lỗi, không crash, trả list rỗng.
   - Parse ngày bằng `parsedate_to_datetime`.
3. Viết CLI:
   - `--source`, default `demo`.
   - `--url`, required.
   - `--limit`, default `5`.
4. In ra từng bài theo format:

```text
[demo] Title - https://...
```

**Command tự kiểm tra:**

```bash
python practice_rss_crawler.py --source vnexpress --url https://vnexpress.net/rss/thoi-su.rss --limit 5
```

**Kết quả đúng:** có tối đa 5 dòng article, mỗi dòng có source, title, URL. Nếu đổi URL thành URL sai, chương trình không văng traceback dài.

**So sánh dự án:** mở `app/crawler.py`, tìm function `fetch_feed()`. So sánh cách dự án xử lý entry, parse category, parse date.

Checklist qua chặng:

- Bạn giải thích được RSS dùng để làm gì.
- Bạn biết `async/await` ở mức đủ dùng.
- Bạn biết `asyncio.gather()` chạy nhiều coroutine song song.
- Bạn parse được ngày tháng từ RSS.
- Bạn tự code được function lấy article candidate từ RSS.
- Bạn chạy được CLI có `--url` và `--limit`.

---

## Chặng 3 - URL Cleanup, Robots Và Rate Limit

**Mục tiêu:** biến crawler từ "request được" thành crawler có trách nhiệm: không crawl trùng, không spam server, biết tôn trọng robots.txt.

### Bạn cần hiểu gì?

- Một URL có các phần: scheme (`https`), domain (`vnexpress.net`), path (`/thoi-su/tin-abc`), query (`?id=1&utm_source=fb`), fragment (`#comment`).
- Query tracking như `utm_source`, `utm_medium`, `fbclid` không làm thay đổi nội dung bài báo → cần bỏ để dedupe.
- **Canonical URL** là URL đã được làm sạch: bỏ tracking, bỏ fragment, sort query, lowercase domain.
- **robots.txt** là file trên mỗi website (ví dụ `https://vnexpress.net/robots.txt`) nói crawler được/không được crawl path nào.
  - `Disallow: /admin/` nghĩa là không được crawl path `/admin/`.
  - `Allow: /` nghĩa là được crawl mọi path.
  - Python có `urllib.robotparser.RobotFileParser` để check.
- **Rate limit** giúp cùng một host không bị request quá nhanh (ví dụ chờ ít nhất 1 giây giữa 2 request cùng domain).
- **Retry** dùng khi gặp lỗi tạm thời:
  - HTTP 429 (Too Many Requests)
  - HTTP 500/502/503 (Server Error)
  - Timeout
  - Dùng exponential backoff: chờ 1s, 2s, 4s, 8s... giữa các lần retry.
- `tenacity` là thư viện retry phổ biến trong dự án.

### File/function trong dự án

- `app/crawler.py`
  - `_TRACKING_PREFIXES`: tuple các prefix tracking cần bỏ (utm_, ga_, fbclid, gclid, ...).
  - `canonicalize_url(url)`: bỏ tracking params, fragment, sort query, lowercase.
  - `url_hash(url)`: SHA-256 của canonical URL, lấy 32 ký tự đầu → tạo ID ổn định.
  - `RobotsCache`: cache robots.txt theo host, check `can_fetch(url)`.
  - `PoliteClient.get()`: request HTTP có timeout, retry (tenacity), rate limit per-host.

### Bài tập nhỏ 3.1 - Tách thành phần URL

**Yêu cầu:** dùng `urllib.parse.urlsplit()` để in `scheme`, `netloc`, `path`, `query`, `fragment` của URL:

```text
https://example.com/news/a?id=1&utm_source=fb#comment
```

**Đáp án gợi ý:**

```python
from urllib.parse import urlsplit

parts = urlsplit("https://example.com/news/a?id=1&utm_source=fb#comment")
print(parts.scheme)    # https
print(parts.netloc)    # example.com
print(parts.path)      # /news/a
print(parts.query)     # id=1&utm_source=fb
print(parts.fragment)  # comment
```

### Bài tập nhỏ 3.2 - Canonical URL

**Yêu cầu:** viết `canonicalize_url(url)`:

- Bỏ fragment `#...`.
- Bỏ query key bắt đầu bằng `utm_`.
- Bỏ `fbclid`, `gclid`, `ref`, `src`, `from`.
- Sort query params theo key.
- Bỏ dấu `/` cuối path, trừ khi path chỉ là `/`.
- Lowercase scheme và domain.

**Đáp án gợi ý:**

```python
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_PREFIXES = ("utm_", "ga_", "yclid", "fbclid", "gclid", "ref", "src", "from")

def canonicalize_url(url):
    parts = urlsplit(url.strip())
    query_items = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if any(lower_key.startswith(prefix) or lower_key == prefix for prefix in TRACKING_PREFIXES):
            continue
        query_items.append((key, value))
    query = urlencode(sorted(query_items))
    path = parts.path
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))
```

**Kết quả đúng:**

```python
assert canonicalize_url("https://A.com/news/?utm_source=x&id=1#top") == "https://a.com/news?id=1"
```

### Bài tập nhỏ 3.3 - Hash URL

**Yêu cầu:** viết `url_hash(url)` dùng SHA-256 của canonical URL, lấy 32 ký tự đầu.

**Đáp án gợi ý:**

```python
import hashlib

def url_hash(url):
    clean = canonicalize_url(url)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:32]
```

**Kết quả đúng:**

```python
u1 = "https://a.com/news?id=1&utm_source=fb"
u2 = "https://a.com/news?id=1"
assert url_hash(u1) == url_hash(u2)
```

### Bài tập nhỏ 3.4 - Kiểm tra robots.txt

**Yêu cầu:** viết function `check_robots(robots_url, target_url, user_agent)` kiểm tra xem URL có được crawl không.

**Đáp án gợi ý:**

```python
from urllib.robotparser import RobotFileParser
import httpx

def check_robots(robots_url, target_url, user_agent="my-bot/1.0"):
    parser = RobotFileParser(robots_url)
    try:
        response = httpx.get(robots_url, timeout=10)
        parser.parse(response.text.splitlines())
    except Exception:
        return True  # Nếu không đọc được robots.txt, mặc định cho phép
    return parser.can_fetch(user_agent, target_url)

# Test
allowed = check_robots(
    "https://vnexpress.net/robots.txt",
    "https://vnexpress.net/thoi-su/tin-abc-123.html",
)
print(f"Allowed: {allowed}")
```

**Liên hệ dự án:** mở `app/crawler.py`, tìm class `RobotsCache`. Dự án cache robots.txt theo host để không phải request lại mỗi lần. Logic tương tự nhưng dùng async và có dict cache.

### Bài tập nhỏ 3.5 - Rate limiter đơn giản

**Yêu cầu:** viết class `SimpleRateLimiter`:

- Có dict lưu lần request cuối của từng host.
- Nếu host vừa được request dưới 1 giây trước, sleep phần còn thiếu.
- Dùng async `await asyncio.sleep(...)`.

**Đáp án gợi ý:**

```python
import asyncio
import time

class SimpleRateLimiter:
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self.last_seen = {}

    async def wait(self, host):
        now = time.monotonic()
        last = self.last_seen.get(host)
        if last is not None:
            delay = self.min_interval - (now - last)
            if delay > 0:
                await asyncio.sleep(delay)
        self.last_seen[host] = time.monotonic()
```

### Bài tập nhỏ 3.6 - Retry với tenacity

**Yêu cầu:** viết function `fetch_with_retry(url)` dùng tenacity retry 3 lần với exponential backoff khi gặp `httpx.HTTPError`.

**Đáp án gợi ý:**

```python
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def fetch_with_retry(url):
    response = httpx.get(url, timeout=10)
    if response.status_code == 429 or response.status_code >= 500:
        raise httpx.HTTPStatusError(
            f"retryable {response.status_code}",
            request=response.request,
            response=response,
        )
    return response.text

# Test
try:
    text = fetch_with_retry("https://example.com")
    print(f"OK, length={len(text)}")
except Exception as e:
    print(f"Failed after retries: {e}")
```

**Liên hệ dự án:** mở `app/crawler.py`, tìm class `PoliteClient`. Method `get()` dùng `AsyncRetrying` (async version) của tenacity với pattern tương tự.

### Bài cuối chặng 3 - Code lại URL tools và polite client mini

**Bối cảnh:** crawler thật cần URL sạch để dedupe và client lịch sự để tránh request quá nhanh.

**File tự tạo:** `practice_url_tools.py`.

**Yêu cầu cụ thể:**

1. Viết `canonicalize_url(url)` theo yêu cầu bài 3.2.
2. Viết `url_hash(url)` theo yêu cầu bài 3.3.
3. Viết `host_from_url(url)` trả domain lowercase.
4. Viết `SimpleRateLimiter` async.
5. Viết `PoliteClientMini`:
   - Dùng `httpx.AsyncClient`.
   - Trước khi request thì gọi rate limiter theo host.
   - Có timeout 10 giây.
   - Nếu status code là `429` hoặc `5xx`, retry tối đa 2 lần.
   - Nếu vẫn lỗi, return `None` thay vì crash.
6. Viết CLI test nhanh 2 URL.

**Command tự kiểm tra:**

```bash
python practice_url_tools.py --url https://example.com/?utm_source=x#top
```

**Kết quả đúng:**

- In URL đã canonical.
- In hash 32 ký tự.
- Request hợp lệ trả text length.
- URL lỗi không làm chương trình crash.

**So sánh dự án:** mở `app/crawler.py` và so sánh:
- `canonicalize_url()` (dòng khoảng 200+)
- `url_hash()` (ngay sau canonicalize)
- `PoliteClient` class (dòng khoảng 89+)

Checklist qua chặng:

- Bạn biết URL canonical dùng để dedupe.
- Bạn biết vì sao cần rate limit và robots.txt.
- Bạn tự code được hash ổn định cho article ID.
- Bạn hiểu retry exponential backoff và tenacity.
- Bạn hiểu ý tưởng chính của `PoliteClient` trong dự án.

---

## Chặng 4 - Extract Nội Dung Bài Báo Từ HTML

**Mục tiêu:** từ HTML nhiều menu/quảng cáo/footer lấy ra phần nội dung bài báo sạch trong `content_text`.

### Bạn cần hiểu gì?

- HTML của một trang báo không chỉ có nội dung bài viết, còn có menu, script, quảng cáo, bài liên quan.
- Model summarization cần text sạch, không cần HTML tag.
- **trafilatura** là thư viện chuyên lấy nội dung chính từ trang web. Cách dùng đơn giản: `trafilatura.extract(html)`.
- **readability-lxml** là fallback nếu trafilatura không extract được. Dùng: `Document(html).summary()` rồi parse bằng BeautifulSoup.
- **BeautifulSoup** dùng để parse HTML và lấy text.
- **Normalize text:**
  - Unicode NFC normalization: `unicodedata.normalize("NFC", text)` đảm bảo ký tự tiếng Việt thống nhất (ví dụ "ả" có thể được biểu diễn bằng 1 hoặc 2 ký tự Unicode).
  - Gộp whitespace: `re.sub(r"\s+", " ", text)`.
  - Strip đầu/cuối.
- **Bỏ boilerplate:** dòng bắt đầu bằng "đọc thêm", "xem thêm", "tags:", "từ khóa:" không phải nội dung bài.
- Crawler nên bỏ bài quá ngắn (ví dụ dưới 50 từ) vì không đủ thông tin để summarize/label.

### File/function trong dự án

- `app/crawler.py`
  - `ExtractedArticle`: dataclass chứa kết quả extract (title, author, published_at, language, content_text, word_count).
  - `normalize_text(text)`: NFC normalize, gộp whitespace, strip.
  - `word_count(text)`: đếm số từ.
  - `extract_from_html(html, url)`: lấy title/content/date bằng trafilatura trước, fallback readability + BeautifulSoup.
  - `_BOILERPLATE_RE`: regex bỏ dòng boilerplate.

### Bài tập nhỏ 4.1 - Lấy text từ HTML đơn giản bằng BeautifulSoup

**Yêu cầu:** với HTML sau, lấy text trong `<article>`:

```html
<html>
  <body>
    <nav>Menu không lấy</nav>
    <article>
      <h1>Tiêu đề bài viết</h1>
      <p>Đoạn một của bài viết.</p>
      <p>Đoạn hai của bài viết.</p>
    </article>
    <footer>Footer không lấy</footer>
  </body>
</html>
```

**Đáp án gợi ý:**

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
article = soup.find("article")
text = article.get_text(" ", strip=True)
print(text)
```

**Kết quả đúng:** output có tiêu đề và 2 đoạn, không có menu/footer.

### Bài tập nhỏ 4.2 - Dùng trafilatura extract nội dung

**Yêu cầu:** tạo `practice_trafilatura.py`, fetch HTML thật từ một URL tin tức, dùng trafilatura extract nội dung.

**Đáp án gợi ý:**

```python
import httpx
import trafilatura

url = "https://vnexpress.net/thoi-su"  # Hoặc URL bài viết cụ thể
response = httpx.get(url, timeout=15, follow_redirects=True)
text = trafilatura.extract(response.text)
if text:
    print(f"Extracted {len(text.split())} words")
    print(text[:200])
else:
    print("trafilatura returned None")
```

**Kết quả đúng:** thấy nội dung text sạch, không có HTML tag, menu, quảng cáo.

### Bài tập nhỏ 4.3 - Fallback: readability + BeautifulSoup

**Yêu cầu:** nếu trafilatura trả `None`, dùng readability-lxml làm fallback.

**Đáp án gợi ý:**

```python
from readability import Document
from bs4 import BeautifulSoup
import trafilatura

def extract_text(html):
    # Try trafilatura first
    text = trafilatura.extract(html)
    if text and len(text.split()) > 20:
        return text
    # Fallback to readability
    doc = Document(html)
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "html.parser")
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    fallback = " ".join(p for p in paragraphs if p)
    return fallback if fallback else None
```

**Liên hệ dự án:** mở `app/crawler.py`, tìm `extract_from_html()`. Dự án dùng pattern tương tự: trafilatura trước, readability + BeautifulSoup fallback.

### Bài tập nhỏ 4.4 - Normalize text (Unicode NFC + whitespace)

**Yêu cầu:** viết `normalize_text(text)`:

- Nếu `None` hoặc chuỗi rỗng thì trả `""`.
- `unicodedata.normalize("NFC", text)` để chuẩn hóa Unicode tiếng Việt.
- Đổi nhiều whitespace liên tiếp thành một space.
- Strip đầu/cuối.

**Đáp án gợi ý:**

```python
import re
import unicodedata

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

**Kết quả đúng:**

```python
assert normalize_text(" A\n\n B   C ") == "A B C"
assert normalize_text(None) == ""
```

**Tại sao cần NFC?** Tiếng Việt có dấu thanh (ả, ã, ắ...) có thể biểu diễn bằng 1 ký tự (precomposed) hoặc 2 ký tự (base + combining mark). NFC đảm bảo luôn dùng precomposed, giúp so sánh text chính xác.

### Bài tập nhỏ 4.5 - Bỏ dòng boilerplate

**Yêu cầu:** viết `remove_boilerplate(text)` bỏ dòng bắt đầu bằng "đọc thêm", "xem thêm", "tags:", "từ khóa:", "liên quan:".

**Đáp án gợi ý:**

```python
import re

_BOILERPLATE_RE = re.compile(
    r"(?im)^\s*(?:đọc thêm|xem thêm|tags?:|từ khóa:|liên quan:).*$"
)

def remove_boilerplate(text):
    return _BOILERPLATE_RE.sub("", text).strip()
```

**Kết quả đúng:**

```python
text = "Nội dung bài.\nĐọc thêm: bài liên quan\nCuối bài."
assert "Đọc thêm" not in remove_boilerplate(text)
```

**Liên hệ dự án:** mở `app/crawler.py`, tìm `_BOILERPLATE_RE`. Pattern tương tự.

### Bài tập nhỏ 4.6 - Bỏ bài quá ngắn

**Yêu cầu:** viết `word_count(text)` và nếu text dưới 50 từ thì return `None`.

**Đáp án gợi ý:**

```python
def word_count(text):
    return len(normalize_text(text).split())

def keep_if_long_enough(text, min_words=50):
    text = normalize_text(text)
    if word_count(text) < min_words:
        return None
    return text
```

### Bài cuối chặng 4 - Code lại extractor mini

**Bối cảnh:** sau khi có URL bài báo, crawler fetch HTML và cần tạo `content_text` sạch.

**File tự tạo:** `practice_extract.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `ExtractedArticle`:
   - `title: str | None`
   - `content_text: str`
   - `word_count: int`
   - `published_at: str | None = None`
2. Viết `normalize_text(text)` với NFC normalization.
3. Viết `remove_boilerplate(text)`.
4. Viết `word_count(text)`.
5. Viết `extract_from_html(html, min_words=50)`:
   - Nếu input rỗng, return `None`.
   - Ưu tiên dùng `trafilatura.extract(html)`.
   - Nếu trafilatura trả `None` hoặc quá ngắn, fallback dùng readability + BeautifulSoup.
   - Normalize text.
   - Bỏ boilerplate.
   - Nếu dưới `min_words`, return `None`.
   - Lấy title từ HTML nếu có.
   - Nếu đạt, return `ExtractedArticle`.
6. CLI test: nhận URL, fetch HTML, extract và in kết quả.

**Command tự kiểm tra:**

```bash
python practice_extract.py --url https://vnexpress.net/thoi-su/tin-abc-123.html
```

**Kết quả đúng:**

- Có title, word_count, đoạn đầu content_text.
- Không có HTML tag, menu, footer, boilerplate.
- Bài quá ngắn trả `None`.

**So sánh dự án:** mở `app/crawler.py`, tìm `extract_from_html()` và so sánh.

Checklist qua chặng:

- Bạn phân biệt được HTML và article text.
- Bạn biết dùng trafilatura và fallback readability.
- Bạn hiểu Unicode NFC normalization.
- Bạn tự code được extractor đầy đủ.

---

## Chặng 5 - SimHash, Dedupe Và Crawl Pipeline Hoàn Chỉnh

**Mục tiêu:** ghép các phần đã học thành crawler tạo được JSONL bài báo: discover RSS → lọc URL → fetch HTML → extract text → dedupe → save.

### Bạn cần hiểu gì?

- **Pipeline** là chuỗi nhiều bước, mỗi bước nhận input và tạo output cho bước sau.
- **Dedupe URL** dùng set/hash để bỏ bài trùng link (2 URL khác tracking params = cùng bài).
- **Dedupe content** (near-duplicate) dùng **SimHash** để bỏ bài nội dung gần giống nhau:
  - Ví dụ: VnExpress và Tuoi Tre cùng đăng tin từ TTXVN → nội dung gần giống.
  - **SimHash** là fingerprint 64-bit của text: chia text thành n-gram, hash mỗi n-gram, kết hợp.
  - **Hamming distance** đo số bit khác nhau giữa 2 SimHash. Nếu distance nhỏ (ví dụ ≤ 3) → bài gần trùng.
- **asyncio.Semaphore** giới hạn số coroutine chạy đồng thời (ví dụ tối đa 5 bài đang fetch cùng lúc).
- **asyncio.Lock** đảm bảo chỉ 1 coroutine truy cập tài nguyên tại một thời điểm.
- Crawl stats giúp biết crawler đang làm gì: discovered, fetched, extracted, skipped.
- `--limit` nên là limit tổng số bài output, không phải limit số RSS item đọc.

### File/function trong dự án

- `app/crawler.py`
  - `simhash64(text)`: tạo fingerprint 64-bit từ text.
  - `hamming(a, b)`: đếm số bit khác nhau giữa 2 hash → `bin(a ^ b).count("1")`.
  - `_SIMHASH_TOKEN_RE`, `_SIMHASH_NGRAM_WIDTH`, `_SIMHASH_WEIGHT_CAP`: cấu hình SimHash.
  - `crawl_articles(...)`: pipeline crawl chính.
  - `write_jsonl(...)`: ghi output.
  - `_run_cli(...)`: command `python -m app.crawler ...`.
- `app/sources.py`
  - `CrawlStats`: dataclass đếm số bài ở mỗi bước pipeline.

### Bài tập nhỏ 5.1 - Dedupe URL bằng set

**Yêu cầu:** với list URL có trùng tracking params, chỉ giữ URL unique theo canonical URL.

**Đáp án gợi ý:**

```python
seen = set()
unique = []
for url in urls:
    clean = canonicalize_url(url)
    if clean in seen:
        continue
    seen.add(clean)
    unique.append(clean)
```

**Kết quả đúng:** hai URL chỉ khác `utm_source` chỉ còn một.

### Bài tập nhỏ 5.2 - Hiểu SimHash

**Lý thuyết nhanh:**

SimHash hoạt động theo các bước:
1. Chia text thành token (từ).
2. Tạo n-gram từ token (ví dụ 4-gram: `["abc def ghi jkl", "def ghi jkl mno", ...]`).
3. Hash mỗi n-gram thành số 64-bit.
4. Với mỗi bit position (0-63): nếu bit = 1 thì +weight, nếu bit = 0 thì -weight.
5. Bit cuối cùng: nếu tổng > 0 thì 1, ngược lại 0.

**Yêu cầu:** viết `simhash_simple(text)` trả fingerprint 64-bit.

**Đáp án gợi ý:**

```python
import hashlib
import re

def simhash_simple(text):
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0
    # Tạo 4-gram
    ngrams = []
    for i in range(len(tokens) - 3):
        ngrams.append(" ".join(tokens[i:i+4]))
    if not ngrams:
        ngrams = tokens  # Fallback nếu text quá ngắn

    v = [0] * 64
    for ngram in ngrams:
        h = int(hashlib.md5(ngram.encode()).hexdigest(), 16) & ((1 << 64) - 1)
        for i in range(64):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint

def hamming_distance(a, b):
    return bin(a ^ b).count("1")

# Test
h1 = simhash_simple("Hà Nội mưa lớn trong nhiều giờ đồng hồ gây ngập úng")
h2 = simhash_simple("Hà Nội mưa lớn trong nhiều giờ liền gây ngập úng")
h3 = simhash_simple("Đội tuyển Việt Nam thắng trận giao hữu tối qua")
print(f"h1 vs h2 (similar): {hamming_distance(h1, h2)}")
print(f"h1 vs h3 (different): {hamming_distance(h1, h3)}")
```

**Kết quả đúng:** `h1 vs h2` có hamming distance nhỏ (≤ 5), `h1 vs h3` có hamming distance lớn (> 10).

**Liên hệ dự án:** mở `app/crawler.py`, tìm `simhash64()`. Dự án dùng thư viện `simhash` thay vì tự viết, nhưng logic tương tự. Dự án coi hamming distance ≤ 3 là near-duplicate.

### Bài tập nhỏ 5.3 - asyncio.Semaphore

**Yêu cầu:** dùng `asyncio.Semaphore(2)` để chỉ cho tối đa 2 coroutine chạy cùng lúc.

**Đáp án gợi ý:**

```python
import asyncio
import time

async def task(name, semaphore):
    async with semaphore:
        print(f"[{time.monotonic():.1f}] {name} start")
        await asyncio.sleep(1)
        print(f"[{time.monotonic():.1f}] {name} done")

async def main():
    sem = asyncio.Semaphore(2)
    await asyncio.gather(
        task("A", sem),
        task("B", sem),
        task("C", sem),
        task("D", sem),
    )

asyncio.run(main())
```

**Kết quả đúng:** A và B bắt đầu cùng lúc, C và D đợi đến khi A hoặc B xong mới bắt đầu.

**Liên hệ dự án:** mở `labeling/label_dataset.py` dòng 93, `asyncio.Semaphore(max(concurrency, 1))` giới hạn số bài label cùng lúc để không vượt quota API.

### Bài tập nhỏ 5.4 - Stats object

**Yêu cầu:** tạo dataclass `CrawlStats` có `discovered`, `fetched`, `extracted`, `fetch_failed`, `extract_failed`, rồi tăng số trong pipeline giả.

**Đáp án gợi ý:**

```python
from dataclasses import dataclass, field

@dataclass
class CrawlStats:
    discovered: int = 0
    fetched: int = 0
    extracted: int = 0
    fetch_failed: int = 0
    extract_failed: int = 0
    errors: list[str] = field(default_factory=list)
```

### Bài tập nhỏ 5.5 - Pipeline giả không dùng internet

**Yêu cầu:** tạo list 5 candidate fake, trong đó:

- 1 URL trùng.
- 1 HTML quá ngắn.
- 1 HTML lỗi `None`.

Pipeline cần output đúng 2 bài hợp lệ.

**Đáp án/kết quả đúng:**

```python
assert stats.discovered == 5
assert stats.extracted == 2
assert len(articles) == 2
```

### Bài tập nhỏ 5.6 - Ghi crawler output JSONL

**Yêu cầu:** mỗi output row có schema tối thiểu:

```json
{"article_id":"...","source":"demo","url":"...","title":"...","content_text":"..."}
```

**Kết quả đúng:** file JSONL có số dòng bằng số article extracted.

### Bài cuối chặng 5 - Code lại crawler mini hoàn chỉnh

**Bối cảnh:** đây là bản thu nhỏ của `app/crawler.py`.

**File tự tạo:** `mini_crawler.py`.

**Yêu cầu cụ thể:**

1. CLI hỗ trợ:
   - `--rss`: RSS URL bắt buộc.
   - `--source`: default `demo`.
   - `--limit`: default `5`.
   - `--output`: default `data/practice/articles.jsonl`.
   - `--verbose`: nếu bật thì in log từng bước.
2. Reuse hoặc tự viết lại:
   - `canonicalize_url()`.
   - `url_hash()`.
   - `fetch_feed()`.
   - `extract_from_html()` (dùng trafilatura + fallback).
   - `normalize_text()`.
   - `write_jsonl()`.
3. Pipeline:
   - Đọc RSS.
   - Duyệt từng candidate.
   - Bỏ URL trùng (dùng set + canonical URL).
   - Fetch HTML.
   - Extract text.
   - Bỏ bài dưới 50 từ.
   - (Bonus) Dedupe content bằng SimHash.
   - Ghi JSONL khi đủ `limit` bài.
4. Mỗi record output cần có:
   - `article_id` (dùng `url_hash()`)
   - `source`
   - `url`
   - `title`
   - `category`
   - `published_at`
   - `content_text`
   - `word_count`
5. Nếu một URL lỗi, bỏ qua và tiếp tục.
6. Cuối chương trình in stats.

**Command tự kiểm tra:**

```bash
python mini_crawler.py --rss https://vnexpress.net/rss/thoi-su.rss --source vnexpress --limit 5 --output data/practice/articles.jsonl --verbose
```

**Kết quả đúng:**

- File `data/practice/articles.jsonl` tồn tại.
- File có tối đa 5 dòng.
- Mỗi dòng có đủ key bắt buộc.
- Terminal in stats kiểu:

```text
discovered=...
fetched=...
extracted=5
```

**So sánh dự án:** mở `app/crawler.py`, đọc function `crawl_articles()` (pipeline chính) và `_run_cli()` (CLI wrapper). So sánh luồng xử lý.

Checklist qua chặng:

- Bạn hiểu SimHash dùng để phát hiện bài gần giống nhau.
- Bạn biết dùng `asyncio.Semaphore` để giới hạn concurrency.
- Bạn tự ghép được crawler từ các function nhỏ.
- Bạn hiểu vì sao live crawl không thể ra đúng lại dataset lịch sử.
- Bạn biết debug khi crawler chạy lâu: bật `--verbose`, giảm `--limit`, crawl từng source.
- Bạn đã đủ nền để đọc gần như toàn bộ `app/crawler.py`.

---

## Chặng 6 - Prompt, JSON Parser Và Gemini Labeling (AI Studio)

**Mục tiêu:** hiểu cách dùng Gemini làm teacher model để tạo summary label cho dataset train ViT5. Hiểu cách gọi AI Studio API, xoay vòng key, xử lý model fallback.

### Bạn cần hiểu gì?

- Trong dự án này, Gemini không phải model chạy web demo cuối cùng.
- Gemini đóng vai trò **teacher**: đọc bài báo và tạo summary chất lượng cao.
- ViT5 đóng vai trò **student**: học lại từ dataset đã được Gemini gán nhãn.
- Prompt cần rõ schema output để parser đọc được.
- LLM có thể trả JSON lỗi, thiếu field, `confidence` quá lớn, hoặc refusal.
- Parser phải robust để pipeline không chết vì một output lỗi.
- Gọi nhiều bài cùng lúc cần giới hạn concurrency (Semaphore) để không vượt quota.
- **AI Studio vs Vertex AI:**
  - **AI Studio**: dùng API key miễn phí từ https://aistudio.google.com/apikey. Có rate limit per-key.
  - **Vertex AI**: dùng GCP project, trả phí theo token. Không cần API key nhưng cần service account.
  - Dự án chuyển sang AI Studio mặc định vì miễn phí.
- **Key rotation:** AI Studio free key có rate limit. Giải pháp:
  - Tạo nhiều key (comma-separated).
  - Khi key hiện tại bị 429 (quota), tự động chuyển sang key tiếp theo.
  - Khi tất cả key hết quota, thử model fallback (ví dụ: gemini-2.5-flash → gemini-2.0-flash).
- **Model fallback:** nếu model mới chưa available, tự động thử model cũ hơn.
- **`google.genai` SDK:** thư viện chính thức mới nhất của Google cho AI Studio.
- **`asyncio.to_thread()`:** chạy function sync (labeler.generate) trong thread riêng để không block event loop.

### File/function trong dự án

- `labeling/prompt.py`
  - `PROMPT_VERSION = "1.2.0"`: version prompt hiện tại.
  - `PROMPT_MODEL = "gemini-2.5-flash"`: model mặc định.
  - `PROMPT_PROVIDER = "aistudio"`: provider mặc định.
  - `SYSTEM_PROMPT`: vai trò và quy tắc cho Gemini (biên tập viên, 2-3 câu, 40-70 từ, trung lập...).
  - `USER_TEMPLATE`: template chứa title/content bài báo + yêu cầu output JSON.
  - `GenerationParams`: dataclass config (temperature=0.2, top_p=0.9, max_output_tokens=4096, response_mime_type="application/json").
  - `QcConfig`: config cho QC (min_words, max_words, min_sentences...).
  - `LabelOutput`: Pydantic model cho output label (summary, key_entities, confidence, refusal_reason).
  - `render_user_prompt(...)`: ghép dữ liệu article vào prompt, cắt content tối đa 6000 ký tự.
  - `parse_label_json(...)`: parse JSON output robust (xử lý confidence clamp, refusal, strict=False fallback).
- `labeling/gemini_labeler.py` (MỚI - thay thế Vertex cho labeling)
  - `GeminiLabeler`: class chính, gọi AI Studio API.
    - `__init__(api_keys, model_chain, params, override_callable)`.
    - `generate(system, user)`: gọi API, per-call local iteration qua keys (thread-safe, không shared state), fallback model.
    - `_get_client(api_key)`: cache client per-key (thread-safe bằng Lock).
  - `_keys_from_env()`: đọc key từ `GEMINI_API_KEYS` hoặc `GEMINI_API_KEY`.
- `labeling/vertex_labeler.py` (legacy, trả phí)
  - `VertexLabeler`: wrapper cũ dùng Vertex AI.
- `labeling/label_dataset.py`
  - `_label_one(row, labeler, semaphore)`: label một article (render prompt → generate → parse → QC).
  - `label_rows(rows, concurrency, limit, labeler, backend)`: label nhiều article bằng asyncio.gather + Semaphore.
  - CLI: `--input`, `--output`, `--limit`, `--concurrency`, `--backend {aistudio,vertex}`.

### Bài tập nhỏ 6.1 - Render prompt từ template

**Yêu cầu:** viết function `render_prompt(title, category, source, content_text)` trả về prompt có format:

```text
Tiêu đề: <title>
Chuyên mục: <category>
Nguồn: <source>

Nội dung:
"""
<content_text>
"""

Trả về JSON đúng schema:
{"summary": "...", "key_entities": ["..."], "confidence": 0.0, "refusal_reason": null}
```

Nếu content dài hơn 6000 ký tự, cắt tại word boundary và thêm `[...]`.

**Đáp án gợi ý:**

```python
TEMPLATE = """Tiêu đề: {title}
Chuyên mục: {category}
Nguồn: {source}

Nội dung:
\"\"\"
{content_text}
\"\"\"

Trả về JSON đúng schema:
{{"summary": "...", "key_entities": ["..."], "confidence": 0.0, "refusal_reason": null}}"""

def render_prompt(title, category, source, content_text, max_chars=6000):
    snippet = content_text or ""
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rsplit(" ", 1)[0] + " [...]"
    return TEMPLATE.format(
        title=title or "",
        category=category or "",
        source=source or "",
        content_text=snippet,
    )
```

**Liên hệ dự án:** mở `labeling/prompt.py` dòng 24-41 (`USER_TEMPLATE`) và dòng 68-84 (`render_user_prompt()`). Logic tương tự.

### Bài tập nhỏ 6.2 - Fake LLM trả JSON

**Yêu cầu:** không gọi API thật. Viết `fake_llm(prompt)` trả string JSON:

```json
{"summary":"Đây là tóm tắt mẫu.","key_entities":["Demo"],"confidence":0.8}
```

**Đáp án gợi ý:**

```python
import json

def fake_llm(prompt):
    return json.dumps(
        {
            "summary": "Đây là tóm tắt mẫu.",
            "key_entities": ["Demo"],
            "confidence": 0.8,
        },
        ensure_ascii=False,
    )
```

### Bài tập nhỏ 6.3 - Parser JSON robust

**Yêu cầu:** viết `parse_label_json(raw)` xử lý các case:

1. JSON hợp lệ có summary và confidence → parse bình thường.
2. `confidence=8` thì clamp về `1.0`.
3. `confidence=-1` thì clamp về `0.0`.
4. `summary=null` và có `refusal_reason` thì summary thành `""`, refusal hợp lệ.
5. JSON nằm trong markdown fence `` ```json ... ``` `` vẫn parse được (LLM đôi khi wrap trong code block).
6. JSON lỗi thì raise `ValueError` ngắn gọn.

**Đáp án gợi ý:**

```python
import json
import re
from pydantic import BaseModel, Field, ValidationError

class LabelOutput(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    refusal_reason: str | None = None

def parse_label_json(raw):
    # Strip markdown code fence if present
    raw = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            data = json.loads(raw, strict=False)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {exc}") from exc

    if isinstance(data, dict):
        confidence = data.get("confidence")
        if isinstance(confidence, (int, float)) and confidence > 1.0:
            data["confidence"] = 1.0
        if data.get("summary") is None and data.get("refusal_reason"):
            data["summary"] = ""

    try:
        return LabelOutput(**data)
    except ValidationError as exc:
        raise ValueError(f"LLM JSON does not match schema: {exc}") from exc
```

**Kết quả đúng:**

```python
parsed = parse_label_json('{"summary": null, "confidence": 8, "refusal_reason": "too short"}')
assert parsed.summary == ""
assert parsed.confidence == 1.0
assert parsed.refusal_reason == "too short"
```

**So sánh dự án:** mở `labeling/prompt.py` dòng 87-105 (`parse_label_json`). Logic gần giống.

### Bài tập nhỏ 6.4 - Hiểu key rotation (per-call iteration)

**Bối cảnh:** khi nhiều thread cùng gọi API (qua `asyncio.to_thread`), nếu dùng shared state (biến chung) để xoay key thì dễ race condition: thread A đánh dấu key 1 hết quota → thread B đang dùng key 2 nhưng bị đánh dấu nhầm. Giải pháp: mỗi lần gọi `generate()`, copy danh sách key ra biến local rồi iterate qua từng key. Thread-safe vì không chia sẻ state.

**Yêu cầu:** viết function `try_all_keys(keys, model, call_fn)`:

- Nhận list key, model name, và `call_fn(key, model)` giả lập API call.
- Iterate qua từng key, nếu `call_fn` raise `QuotaError` thì thử key tiếp.
- Nếu hết key mà vẫn lỗi, raise `AllKeysExhaustedError`.
- Nếu thành công, return kết quả.

**Đáp án gợi ý:**

```python
class QuotaError(Exception):
    pass

class AllKeysExhaustedError(Exception):
    pass

def try_all_keys(keys, model, call_fn):
    last_exc = None
    for key_idx, key in enumerate(keys):
        try:
            return call_fn(key, model)
        except QuotaError as exc:
            print(f"Key #{key_idx + 1} quota hit, trying next...")
            last_exc = exc
            continue
    raise AllKeysExhaustedError(f"All {len(keys)} keys exhausted. Last: {last_exc}")
```

**Kết quả đúng:**

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

**Tại sao không dùng shared KeyRing?** Khi `concurrency=5`, có 5 thread gọi đồng thời. Nếu dùng shared state, thread A mark key 1 hết → thread B đang dùng key 2 nhưng bị mark nhầm → cả 3 key bị exhausted sai. Per-call iteration tránh hoàn toàn race condition này.

**Liên hệ dự án:** mở `labeling/gemini_labeler.py`, tìm method `generate()`. Dòng `keys = list(self._keys)` tạo local copy, sau đó `for key_idx, api_key in enumerate(keys)` iterate qua từng key mà không chia sẻ state giữa các thread.

### Bài tập nhỏ 6.5 - Gọi AI Studio API (nếu có key)

**Yêu cầu:** nếu bạn có API key AI Studio, thử gọi thật:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_KEY")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Xin chào, bạn là ai?",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=100,
    ),
)
print(response.text)
```

Nếu chưa có key, bỏ qua bài này. Bạn vẫn có thể dùng `override_callable` (fake LLM) để test pipeline.

### Bài tập nhỏ 6.6 - asyncio.to_thread

**Yêu cầu:** viết hàm sync `slow_compute(n)` sleep 1 giây rồi trả `n * 2`. Gọi nó từ async code dùng `asyncio.to_thread()`.

**Đáp án gợi ý:**

```python
import asyncio
import time

def slow_compute(n):
    time.sleep(1)  # Giả lập API call chậm
    return n * 2

async def main():
    # Chạy 3 calls song song nhờ to_thread
    results = await asyncio.gather(
        asyncio.to_thread(slow_compute, 1),
        asyncio.to_thread(slow_compute, 2),
        asyncio.to_thread(slow_compute, 3),
    )
    print(results)  # [2, 4, 6]

asyncio.run(main())
```

**Liên hệ dự án:** mở `labeling/label_dataset.py` dòng 56:
```python
raw = await asyncio.to_thread(labeler.generate, system=SYSTEM_PROMPT, user=user_prompt)
```
`labeler.generate()` là hàm sync (gọi HTTP), nhưng `_label_one()` là async. `to_thread()` chạy hàm sync trong thread pool để không block event loop.

### Bài tập nhỏ 6.7 - Label JSONL bằng fake LLM

**Yêu cầu:** đọc file JSONL có 3 article, mỗi dòng có `title`, `content_text`. Với mỗi dòng:

- Render prompt.
- Gọi `fake_llm(prompt)`.
- Parse output.
- Ghi ra `labeled.jsonl` với các field cũ + `summary`, `key_entities`, `confidence`, `prompt_version`.

**Kết quả đúng:** input 3 dòng tạo output 3 dòng, mỗi dòng có summary.

### Bài cuối chặng 6 - Code lại fake labeling pipeline kiểu dự án

**Bối cảnh:** trước khi gọi API thật, bạn cần hiểu pipeline labeling bằng fake LLM để không bị rối bởi credential/quota.

**File tự tạo:** `practice_label_dataset.py`.

**Yêu cầu cụ thể:**

1. Tạo `PROMPT_VERSION = "practice_v1"`.
2. Tạo `SYSTEM_PROMPT` mô tả vai trò biên tập viên.
3. Tạo `render_user_prompt(title, category, source, content_text)`:
   - Nếu content dài hơn 6000 ký tự thì cắt.
   - Prompt phải yêu cầu output JSON.
4. Tạo Pydantic model `LabelOutput`.
5. Tạo `parse_label_json(raw)` robust theo bài 6.3.
6. Tạo class `FakeLabeler`:
   - `generate(system, user)` return JSON string.
   - Summary lấy 2 câu đầu từ content.
7. Tạo async `label_one(row, labeler, semaphore)`:
   - Nhận dict article.
   - Gọi render prompt → `asyncio.to_thread(labeler.generate, ...)` → parse → return dict mới.
   - Nếu lỗi, return dict có `summary=""`, `qc_passed=False`.
8. Tạo `label_rows(rows, concurrency=3)`:
   - Dùng `asyncio.Semaphore`.
   - `asyncio.gather()` label nhiều dòng.
9. Tạo CLI:

```bash
python practice_label_dataset.py --input data/practice/articles.jsonl --output data/practice/labeled.jsonl --concurrency 3
```

**Schema output bắt buộc:**

```json
{
  "article_id": "...",
  "source": "...",
  "url": "...",
  "title": "...",
  "content_text": "...",
  "summary": "...",
  "key_entities": [],
  "confidence": 0.8,
  "refusal_reason": null,
  "prompt_version": "practice_v1",
  "qc_passed": true
}
```

**Kết quả đúng:**

- Nếu input có 5 dòng, output có 5 dòng.
- Dòng nào content rỗng thì vẫn không crash pipeline; có `refusal_reason`.
- Parser clamp `confidence > 1` về `1.0`.
- Bạn có thể giải thích: thay `FakeLabeler` bằng `GeminiLabeler(api_keys=[...])` là xong.

**So sánh dự án:** mở `labeling/label_dataset.py` toàn bộ file. So sánh `_label_one()`, `label_rows()`, CLI.

Checklist qua chặng:

- Bạn hiểu teacher-student learning ở mức dự án.
- Bạn tự viết được prompt renderer.
- Bạn tự viết được parser JSON robust.
- Bạn hiểu key rotation và model fallback.
- Bạn hiểu `asyncio.to_thread()` dùng khi nào.
- Bạn hiểu vì sao dự án cần `prompt_version`.
- Bạn biết cách chuyển từ fake labeler sang AI Studio thật.

---

## Chặng 7 - QC Và Dataset Split

**Mục tiêu:** lọc summary kém chất lượng và chia dataset train/val/test ổn định.

### Bạn cần hiểu gì?

- Không phải label nào LLM tạo ra cũng nên đưa vào train.
- **QC rule-based** giúp bắt lỗi đơn giản:
  - Summary quá ngắn (< 40 từ) hoặc quá dài (> 90 từ).
  - Summary quá ít câu (< 2) hoặc quá nhiều câu (> 4).
  - **Number faithfulness:** số trong summary phải xuất hiện trong bài gốc (tránh LLM bịa số liệu).
  - **Entity faithfulness:** tên riêng trong summary nên có trong bài gốc (tránh LLM bịa tên).
  - LLM refusal: nếu LLM từ chối tóm tắt → fail.
- **Fuzzy matching** (rapidfuzz): khi kiểm tra entity, không cần exact match 100%. `partial_ratio >= 85%` là chấp nhận được (vì LLM có thể viết tên hơi khác).
- **Split dataset deterministic:** chạy lại vẫn ra cùng train/val/test.
  - Dùng SHA-256 hash của `article_id` để quyết định bucket.
  - Lấy byte đầu tiên: `< 26` → test (~10.2%), `< 52` → val (~10.2%), còn lại → train (~79.7%).
- Dự án dùng artifact JSONL làm source of truth thay vì DB.

### File/function trong dự án

- `labeling/qc.py`
  - `QcResult`: dataclass kết quả QC (passed, reasons, word_count, sentence_count, missing_numbers, missing_entities).
  - `run_qc(output, source_text, cfg)`: chạy tất cả QC checks.
  - `_word_count(text)`, `_sentences(text)`: đếm từ/câu.
  - `_numerics(text)`: tìm token có chứa số.
  - `_contains_numeric(source, token)`: kiểm tra số có trong bài gốc (xử lý dấu chấm phẩy, nhóm chữ số).
  - `_entities(text)`: tìm tên riêng bằng regex (chuỗi từ viết hoa liên tiếp).
  - `_contains_entity(source, entity, min_ratio)`: kiểm tra entity có trong bài gốc (exact match → collapsed punct → fuzzy partial_ratio → token-level).
- `labeling/split_dataset.py`
  - `split_bucket(article_id)`: SHA-256 → quyết định train/val/test.
  - `dataset_record(row)`: giữ field cần cho training.
  - `split_rows(rows)`: chia rows (bỏ qc_failed, bỏ empty content/summary).
  - `export_splits(input_path, output_dir)`: ghi 3 file JSONL.
  - `EXPECTED_V2_COUNTS`: `{"train": 1636, "val": 218, "test": 216}` — artifact lịch sử.

### Bài tập nhỏ 7.1 - Đếm từ và câu

**Yêu cầu:** viết:

- `word_count(text)`.
- `sentence_count(text)` tách câu theo `.`, `!`, `?`, `…`.

**Đáp án gợi ý:**

```python
import re

def word_count(text):
    return len((text or "").split())

def sentence_count(text):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?\u2026])\s+", text or "") if s.strip()]
    return len(sentences)
```

**Kết quả đúng:** summary 2 câu trả `sentence_count == 2`.

### Bài tập nhỏ 7.2 - Check số trong summary

**Yêu cầu:** nếu summary có số `9999` nhưng content không có `9999`, QC fail.

**Đáp án gợi ý:**

```python
import re

def extract_numbers(text):
    return re.findall(r"\S*\d[\S]*", text or "")

def numbers_supported(summary, content):
    for token in extract_numbers(summary):
        cleaned = token.strip(".,;:%()[]{}").strip()
        if not cleaned:
            continue
        if cleaned in content:
            continue
        # Try digit groups
        groups = re.findall(r"\d{3,}", cleaned)
        if groups and all(g in content for g in groups):
            continue
        return False
    return True
```

**Kết quả đúng:**

```python
assert numbers_supported("Có 10 người tham gia.", "Sự kiện có 10 người tham gia.")
assert not numbers_supported("Có 9999 người.", "Sự kiện có 10 người.")
```

**Liên hệ dự án:** mở `labeling/qc.py` dòng 66-87, các function `_numerics()` và `_contains_numeric()`. Logic phức tạp hơn, xử lý thêm dấu chấm, dấu phẩy trong số.

### Bài tập nhỏ 7.3 - Check entity với fuzzy matching

**Yêu cầu:** viết `entity_in_source(entity, source_text, min_ratio=85)`:

- Exact match: entity trong source → True.
- Fuzzy match: dùng `rapidfuzz.fuzz.partial_ratio(entity, source) >= min_ratio` → True.
- Token-level: nếu bất kỳ token ≥ 4 ký tự của entity có trong source → True.

**Đáp án gợi ý:**

```python
from rapidfuzz import fuzz

def entity_in_source(entity, source_text, min_ratio=85):
    if entity in source_text:
        return True
    if fuzz.partial_ratio(entity, source_text) >= min_ratio:
        return True
    return any(len(token) >= 4 and token in source_text for token in entity.split())
```

**Kết quả đúng:**

```python
assert entity_in_source("Hà Nội", "Thủ đô Hà Nội mưa lớn")
assert entity_in_source("Ha Noi", "Thủ đô Hà Nội mưa lớn")  # fuzzy
assert not entity_in_source("Đà Nẵng", "Thủ đô Hà Nội mưa lớn")
```

**Liên hệ dự án:** mở `labeling/qc.py` dòng 101-110 (`_contains_entity`). Pattern tương tự.

### Bài tập nhỏ 7.4 - QC summary đầy đủ

**Yêu cầu:** viết `run_qc(summary, content, refusal_reason=None)`:

- Fail nếu có `refusal_reason`.
- Summary phải 40-90 từ.
- Summary phải 2-4 câu.
- Mọi số trong summary phải có trong content.
- Return `{"passed": bool, "reasons": list[str]}`.

**Đáp án gợi ý:**

```python
def run_qc(summary, content, refusal_reason=None, min_words=40, max_words=90, min_sentences=2, max_sentences=4):
    reasons = []
    if refusal_reason:
        reasons.append(f"llm_refusal:{refusal_reason}")
    wc = word_count(summary)
    if wc < min_words:
        reasons.append(f"too_short:{wc}<{min_words}")
    if wc > max_words:
        reasons.append(f"too_long:{wc}>{max_words}")
    sc = sentence_count(summary)
    if sc < min_sentences:
        reasons.append(f"too_few_sentences:{sc}<{min_sentences}")
    if sc > max_sentences:
        reasons.append(f"too_many_sentences:{sc}>{max_sentences}")
    if not numbers_supported(summary, content):
        reasons.append("unsupported_numbers")
    return {"passed": not reasons, "reasons": reasons}
```

### Bài tập nhỏ 7.5 - Split deterministic

**Yêu cầu:** chia theo `article_id` dùng SHA-256:

- Byte đầu tiên < 26: test (~10%).
- Byte đầu tiên < 52: val (~10%).
- Còn lại: train (~80%).

**Đáp án gợi ý:**

```python
import hashlib

def split_bucket(article_id, salt="vn-news-v1"):
    digest = hashlib.sha256(f"{salt}:{article_id}".encode()).digest()
    bucket = digest[0]
    if bucket < 26:
        return "test"
    if bucket < 52:
        return "val"
    return "train"
```

**Kết quả đúng:** cùng một `article_id` gọi nhiều lần luôn trả cùng split.

**Liên hệ dự án:** mở `labeling/split_dataset.py` dòng 15-22. Logic giống hệt.

### Bài tập nhỏ 7.6 - Dataset record

**Yêu cầu:** từ labeled row có nhiều field, chỉ giữ field dùng cho training:

- `article_id`, `source`, `url`, `title`, `category`, `published_at`, `content_text`, `summary`, `prompt_version`

**Đáp án gợi ý:**

```python
DATASET_FIELDS = [
    "article_id", "source", "url", "title", "category", "published_at",
    "content_text", "summary", "prompt_version",
]

def dataset_record(row):
    return {key: row.get(key, "") for key in DATASET_FIELDS}
```

### Bài cuối chặng 7 - Code lại QC và split dataset

**Bối cảnh:** dataset train chỉ nên chứa bài đã pass QC và có schema ổn định.

**File tự tạo:** `practice_qc_split.py`.

**Yêu cầu cụ thể:**

1. CLI hỗ trợ:

```bash
python practice_qc_split.py --input data/practice/labeled.jsonl --output data/practice/dataset
```

2. Đọc JSONL input.
3. Với mỗi row, chạy QC:
   - Fail nếu `summary` rỗng.
   - Fail nếu có `refusal_reason`.
   - Summary phải 40-90 từ.
   - Summary phải 2-4 câu.
   - Mọi số trong summary phải xuất hiện trong `content_text`.
4. Chỉ giữ row QC pass.
5. Chia train/val/test bằng hash `article_id`.
6. Ghi 3 file:

```text
data/practice/dataset/train.jsonl
data/practice/dataset/val.jsonl
data/practice/dataset/test.jsonl
```

7. Mỗi dòng chỉ giữ dataset fields ở bài 7.6.
8. In report cuối:

```text
total=...
qc_passed=...
train=...
val=...
test=...
```

**Kết quả đúng:**

- Input có summary chứa số bịa thì bị loại.
- Chạy lại cùng input thì số dòng train/val/test không đổi.
- Nếu output folder chưa tồn tại, chương trình tự tạo.
- JSONL output không chứa field thừa như `confidence`, `qc_details`, `label_error`.

**So sánh dự án:** mở `labeling/qc.py` (QC đầy đủ) và `labeling/split_dataset.py` (split logic).

Checklist qua chặng:

- Bạn giải thích được vì sao cần QC trước khi train.
- Bạn hiểu fuzzy matching cho entity check.
- Bạn tự code được split deterministic.
- Bạn hiểu dataset v2 là artifact lịch sử, không bị live crawl ghi đè.

---

## Chặng 8 - Fine-tune ViT5 + LoRA

**Mục tiêu:** hiểu đủ để chạy notebook fine-tune, giải thích được trong CV/phỏng vấn, và biết report metric ROUGE đến từ đâu.

### Bạn cần hiểu gì?

- Summarization trong dự án là bài toán **text-to-text**: input là bài báo, output là summary.
- **Tokenizer** biến text thành token IDs để model đọc.
  - `input_ids`: token của article.
  - `attention_mask`: đánh dấu token thật (1) vs padding (0).
  - `labels`: token của summary (mục tiêu model cần sinh ra).
- **Seq2Seq model** (encoder-decoder) học sinh output sequence mới từ input sequence.
- **ViT5** là T5 model pre-train trên dữ liệu tiếng Việt bởi VietAI.
- **LoRA (Low-Rank Adaptation):**
  - Thay vì update tất cả parameters (full fine-tune), LoRA chỉ thêm adapter nhỏ vào một số layer.
  - `r=16`: rank (kích thước adapter). Nhỏ → ít param, nhanh, nhưng có thể kém hơn.
  - `alpha=32`: scaling factor.
  - `dropout=0.05`: regularization.
  - `target_modules=["q", "v"]`: chỉ thêm adapter vào query và value attention.
  - Lợi ích: train nhanh hơn, nhẹ hơn, checkpoint nhỏ hơn.
- **ROUGE** metrics:
  - ROUGE-1: overlap unigram (từ đơn) giữa prediction và reference.
  - ROUGE-2: overlap bigram (cặp từ liên tiếp).
  - ROUGE-L: longest common subsequence (thứ tự từ).
  - F-measure kết hợp precision và recall.
- **Hyperparameters** quan trọng: model, max lengths, batch size, gradient accumulation, learning rate, epoch, seed.

### File/report trong dự án

- `notebooks/finetune_vit5_lora.ipynb`
  - Notebook fine-tune chính.
  - Tham số được viết trực tiếp trong notebook để dễ show với nhà tuyển dụng.
- `docs/training_report.md` (nếu có)
  - Base model: `VietAI/vit5-base`.
  - LoRA: `r=16`, `alpha=32`, `dropout=0.05`, target `[q, v]`.
  - Best checkpoint: `models/vit5-news-v2/checkpoint-309`.
  - Test ROUGE: `0.6055 / 0.3106 / 0.3804`.

### Bài tập nhỏ 8.1 - Tạo dataset toy

**Yêu cầu:** tạo list 6 sample:

```python
{"text": "Bài viết dài ...", "summary": "Tóm tắt ngắn ..."}
```

Chia 4 train, 1 val, 1 test.

**Đáp án gợi ý:**

```python
samples = [
    {"text": "Hôm nay trời mưa lớn tại Hà Nội trong nhiều giờ.", "summary": "Hà Nội mưa lớn."},
    {"text": "Đội tuyển Việt Nam thắng trận giao hữu với tỷ số 2-0.", "summary": "Việt Nam thắng 2-0."},
    {"text": "Giá vàng tăng mạnh trong phiên giao dịch sáng nay.", "summary": "Giá vàng tăng."},
    {"text": "Bão số 5 đổ bộ vào miền Trung gây thiệt hại lớn.", "summary": "Bão số 5 gây thiệt hại."},
    {"text": "Thủ tướng dự hội nghị quốc tế tại Singapore.", "summary": "Thủ tướng dự hội nghị."},
    {"text": "Mỹ công bố gói viện trợ mới cho Ukraine.", "summary": "Mỹ viện trợ Ukraine."},
]
train_data = samples[:4]
val_data = samples[4:5]
test_data = samples[5:]
print(len(train_data), len(val_data), len(test_data))
```

**Kết quả đúng:** in `4 1 1`.

### Bài tập nhỏ 8.2 - Hiểu tokenizer output

**Yêu cầu:** dùng tokenizer ViT5 từ Hugging Face, tokenize một câu, in `input_ids` và `attention_mask`.

**Đáp án gợi ý:**

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("VietAI/vit5-base")
encoded = tokenizer("Tóm tắt: Đây là một bài báo ngắn.", max_length=32, truncation=True)
print(encoded.keys())          # dict_keys(['input_ids', 'attention_mask'])
print(encoded["input_ids"][:10])
print(encoded["attention_mask"][:10])
print(f"Token count: {len(encoded['input_ids'])}")
```

**Kết quả đúng:** thấy dict có `input_ids`, `attention_mask`. Mỗi phần tử là số nguyên.

### Bài tập nhỏ 8.3 - Tạo preprocessing function

**Yêu cầu:** viết function nhận batch có `content_text` và `summary`, trả tokenized input và labels.

**Đáp án gợi ý:**

```python
def preprocess(batch, tokenizer, max_input=512, max_target=128):
    inputs = ["Tóm tắt: " + text for text in batch["content_text"]]
    model_inputs = tokenizer(inputs, max_length=max_input, truncation=True, padding=True)
    labels = tokenizer(text_target=batch["summary"], max_length=max_target, truncation=True, padding=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs
```

### Bài tập nhỏ 8.4 - Đếm trainable parameters với LoRA

**Yêu cầu:** sau khi bọc model bằng PEFT LoRA, in số parameter trainable.

**Đáp án gợi ý:**

```python
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q", "v"],
    task_type=TaskType.SEQ_2_SEQ_LM,
)

peft_model = get_peft_model(base_model, lora_config)

def print_trainable_parameters(model):
    trainable = 0
    total = 0
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f"trainable={trainable:,} total={total:,} percent={100 * trainable / total:.2f}%")

print_trainable_parameters(peft_model)
```

**Kết quả đúng:** trainable nhỏ hơn total rất nhiều (thường < 1%).

### Bài tập nhỏ 8.5 - Tính ROUGE cho 2 câu

**Yêu cầu:** dùng `rouge_score` tính ROUGE giữa prediction và reference.

**Đáp án gợi ý:**

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)
score = scorer.score("Hà Nội mưa lớn.", "Hà Nội có mưa lớn trong ngày.")
print(f"ROUGE-1: {score['rouge1'].fmeasure:.4f}")
print(f"ROUGE-2: {score['rouge2'].fmeasure:.4f}")
print(f"ROUGE-L: {score['rougeL'].fmeasure:.4f}")
```

### Bài cuối chặng 8 - Tạo notebook mini fine-tune flow

**Bối cảnh:** bạn chưa cần train ra metric đẹp. Mục tiêu là hiểu pipeline notebook từ dataset tới generate/eval.

**File tự tạo:** `notebooks/practice_finetune_flow.ipynb`.

**Yêu cầu cụ thể theo cell:**

1. **Cell 1 - Install/import**
   - Import `transformers`, `datasets`, `rouge_score`, `torch`, `peft`.
2. **Cell 2 - Config viết trực tiếp**
   - `MODEL_NAME = "VietAI/vit5-base"` hoặc model nhỏ hơn nếu máy yếu.
   - `MAX_INPUT_LENGTH = 512`.
   - `MAX_TARGET_LENGTH = 128`.
   - `LEARNING_RATE = 5e-5`.
   - `NUM_EPOCHS = 1`.
   - `SEED = 42`.
3. **Cell 3 - Load dataset toy**
   - Tạo ít nhất 20 sample text-summary.
   - Chia train/val/test.
4. **Cell 4 - Tokenizer/preprocess**
   - Tokenize input và target.
5. **Cell 5 - Load model**
   - Load seq2seq model.
   - Bọc LoRA với config: `r=16`, `alpha=32`, `dropout=0.05`, `target_modules=["q", "v"]`.
   - In trainable parameters.
6. **Cell 6 - TrainingArguments/Trainer**
   - Train 1 epoch.
7. **Cell 7 - Generate thử**
   - Generate summary cho 3 sample.
8. **Cell 8 - Evaluate ROUGE**
   - In dict có `rouge1`, `rouge2`, `rougeL`.
9. **Cell 9 - Ghi chú phỏng vấn**
   - Viết 5 dòng: vì sao dùng ViT5, vì sao dùng LoRA, vì sao dùng ROUGE.

**Kết quả đúng:**

- Notebook chạy tuần tự không lỗi.
- Có cell in dataset size.
- Có cell in trainable parameters.
- Có cell generate summary.
- Có cell tính ROUGE.

Checklist qua chặng:

- Bạn hiểu notebook chính của dự án đang làm gì.
- Bạn giải thích được các hyperparameter quan trọng.
- Bạn biết report training là kết quả lịch sử trên dataset v2 và checkpoint đúng.

---

## Chặng 9 - Inference Với Fine-tuned Model

**Mục tiêu:** load model đã fine-tune và dùng để tóm tắt bài mới, chuẩn bị cho web demo.

### Bạn cần hiểu gì?

- Training là giai đoạn học, inference là giai đoạn dùng model để dự đoán.
- Hugging Face tokenizer phải khớp với model.
- **PEFT adapter loading:**
  - Checkpoint LoRA chỉ chứa adapter weights, không chứa base model weights.
  - Cần load base model trước (`AutoModelForSeq2SeqLM.from_pretrained(base_name)`).
  - Rồi load adapter lên base model (`PeftModel.from_pretrained(base_model, adapter_path)`).
  - `PeftConfig.from_pretrained(adapter_path)` cho biết base model gốc.
  - Nếu adapter folder không có `tokenizer.json`, load tokenizer từ base model.
- **Lazy loading** nghĩa là chưa load model khi import file, chỉ load khi gọi summarize lần đầu.
  - Giúp FastAPI khởi động nhanh.
  - Tránh load model nếu không cần (ví dụ chỉ gọi `/healthz`).
- Batch inference giúp summarize nhiều bài cùng lúc hiệu quả hơn.
- **Generation config** ảnh hưởng output:
  - `num_beams=4`: beam search (nhiều nhánh tìm output tốt nhất).
  - `max_new_tokens=128`: giới hạn độ dài output.
  - `no_repeat_ngram_size=3`: tránh lặp 3-gram.
  - `length_penalty=1.0`: ưu tiên output dài/ngắn hơn.
  - `early_stopping=True`: dừng beam khi tìm đủ.
- Web app không nên crash nếu input rỗng.

### File/function trong dự án

- `app/summarizer.py`
  - `GenerationConfig`: dataclass chứa tham số generate.
  - `ViT5Summarizer`: class load tokenizer/model.
    - `__init__()`: nhận `model_id`, `base_model_id`, `token`, `device`, `generation`. Đọc từ env var nếu không truyền.
    - `_load_as_peft_adapter()`: thử load như LoRA adapter (PeftConfig → base model → PeftModel).
    - `_ensure_loaded()`: lazy load. Thử PEFT trước, fallback load trực tiếp.
    - `summarize(text)`: tóm tắt 1 bài.
    - `summarize_batch(texts)`: tóm tắt nhiều bài, xử lý empty input.

### Bài tập nhỏ 9.1 - Class lazy loading giả

**Yêu cầu:** viết class `LazyObject` chỉ load data khi gọi `get()` lần đầu.

**Đáp án gợi ý:**

```python
class LazyObject:
    def __init__(self):
        self.data = None
        self.load_count = 0

    def _load(self):
        self.load_count += 1
        self.data = {"value": 123}

    def get(self):
        if self.data is None:
            self._load()
        return self.data

obj = LazyObject()
obj.get()
obj.get()
assert obj.load_count == 1
```

### Bài tập nhỏ 9.2 - Summarizer giả không dùng model

**Yêu cầu:** viết `SimpleFakeSummarizer`:

- `summarize(text)` trả 30 từ đầu.
- Input rỗng trả `""`.
- `summarize_batch(texts)` trả list cùng độ dài (input rỗng → `""`).

**Đáp án gợi ý:**

```python
class SimpleFakeSummarizer:
    def summarize(self, text):
        if not text or not text.strip():
            return ""
        return " ".join(text.split()[:30])

    def summarize_batch(self, texts):
        return [self.summarize(text) for text in texts]
```

**Kết quả đúng:**

```python
s = SimpleFakeSummarizer()
assert s.summarize("") == ""
assert len(s.summarize_batch(["a b c", "", "d e"])) == 3
```

### Bài tập nhỏ 9.3 - Load model name từ env

**Yêu cầu:** đọc biến môi trường `HF_MODEL_ID`, nếu không có thì dùng default.

**Đáp án gợi ý:**

```python
import os

model_id = os.environ.get("HF_MODEL_ID", "VietAI/vit5-base")
print(model_id)
```

### Bài tập nhỏ 9.4 - Generation config

**Yêu cầu:** tạo dataclass:

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

Tạo 2 config: default và custom (`max_new_tokens=64`, `num_beams=2`).

### Bài tập nhỏ 9.5 - Hiểu PEFT adapter loading

**Yêu cầu:** viết pseudocode (hoặc code thật nếu có model) cho quy trình load PEFT adapter:

```python
# 1. Thử load PeftConfig để biết base model
# 2. Load base model
# 3. Load adapter lên base model
# 4. Load tokenizer (từ adapter nếu có, nếu không thì từ base)
```

**Đáp án gợi ý:**

```python
from peft import PeftConfig, PeftModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from pathlib import Path

def load_peft_model(adapter_id, base_model_override=None, token=None):
    peft_cfg = PeftConfig.from_pretrained(adapter_id, token=token)
    base_name = base_model_override or peft_cfg.base_model_name_or_path

    base_model = AutoModelForSeq2SeqLM.from_pretrained(base_name, token=token)
    model = PeftModel.from_pretrained(base_model, adapter_id, token=token)

    # Tokenizer: adapter folder nếu có, nếu không thì base model
    tokenizer_source = adapter_id
    if Path(adapter_id).exists() and not (Path(adapter_id) / "tokenizer.json").exists():
        tokenizer_source = base_name
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, token=token)

    return model, tokenizer
```

**Liên hệ dự án:** mở `app/summarizer.py` dòng 48-68 (`_load_as_peft_adapter`). Logic tương tự.

### Bài cuối chặng 9 - Code lại summarizer class kiểu dự án

**Bối cảnh:** web demo cần một class duy nhất để nhận list text và trả list summary.

**File tự tạo:** `practice_inference.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `GenerationConfig` gồm:
   - `max_input_length`, `max_new_tokens`, `num_beams`, `no_repeat_ngram_size`, `length_penalty`, `early_stopping`, `batch_size`
2. Tạo class `SimpleSummarizer`:
   - `__init__(model_id=None, base_model_id=None, token=None, device=None, generation=None)`.
   - Nếu `model_id` không truyền, đọc từ `HF_MODEL_ID`.
   - Có private fields `_model`, `_tokenizer`.
3. Viết `_load_as_peft_adapter()`: thử load LoRA. Return `(model, tokenizer)` hoặc `None`.
4. Viết `_ensure_loaded()`:
   - Thử PEFT trước, fallback load trực tiếp.
   - Gọi nhiều lần không load lại (lazy).
   - `model.eval()` để inference mode.
5. Viết `summarize(text)`:
   - Text rỗng trả `""`.
6. Viết `summarize_batch(texts)`:
   - Return list cùng độ dài input.
   - Phần tử input rỗng trả `""`.
   - Chia batch theo `batch_size`.
7. CLI test:

```bash
USE_FAKE_MODEL=1 python practice_inference.py --text "Một đoạn tin tức dài..."
```

**Kết quả đúng:**

- `summarize("")` trả `""`.
- `summarize_batch(["a", "", "b"])` trả 3 phần tử.
- Log cho thấy model chỉ load một lần.

**So sánh dự án:** mở `app/summarizer.py` toàn bộ file.

Checklist qua chặng:

- Bạn hiểu khác nhau giữa train và inference.
- Bạn biết lazy loading để web khởi động nhẹ hơn.
- Bạn hiểu PEFT adapter loading flow.
- Bạn tự code được interface giống `ViT5Summarizer`.

---

## Chặng 10 - FastAPI Web Demo Và Tích Hợp Toàn Bộ

**Mục tiêu:** ghép crawler và summarizer thành web app: mở trang, bấm nút, crawl tin mới, tóm tắt và hiển thị kết quả.

### Bạn cần hiểu gì?

- FastAPI route `GET /` trả trang HTML (dùng Jinja2 template).
- FastAPI route `GET /healthz` dùng kiểm tra service sống.
- FastAPI route `POST /api/summarize-today` chạy logic chính: crawl → summarize → return JSON.
- Pydantic response model giúp API output rõ schema.
- Jinja2 template render file HTML với biến Python: `{{ model_id }}`, `{{ max_articles }}`.
- Frontend gọi API bằng `fetch()` mà không reload page (AJAX pattern).
- `HTTPException` dùng để trả lỗi API rõ ràng (ví dụ 502 nếu không crawl được, 500 nếu model lỗi).
- **XSS prevention:** `escapeHtml()` trong JavaScript thay thế `<`, `>`, `&`, `"`, `'` để tránh inject HTML/JS.
- Environment variable giúp đổi cấu hình mà không sửa code.

### File/function trong dự án

- `app/main.py`
  - `app = FastAPI(...)`: tạo app.
  - `templates = Jinja2Templates(directory="app/templates")`: mount templates.
  - `summarizer = ViT5Summarizer()`: tạo summarizer global (lazy load).
  - `index()`: render trang web.
  - `healthz()`: trả `{"status":"ok"}`.
  - `summarize_today()`: crawl demo + summarize + return `SummarizeResponse`.
- `app/templates/index.html`
  - Giao diện có button "Tóm tắt tin tức hôm nay".
  - JavaScript gọi `POST /api/summarize-today` bằng `fetch()`.
  - `escapeHtml()` chống XSS.
  - Render kết quả thành cards.
- `Dockerfile`, `docker-compose.yml`
  - Chạy app trong container.

### Bài tập nhỏ 10.1 - FastAPI hello world

**Yêu cầu:** tạo `practice_api.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
```

Chạy:

```bash
uvicorn practice_api:app --reload
```

**Kết quả đúng:** mở `http://127.0.0.1:8000/healthz` thấy JSON.

### Bài tập nhỏ 10.2 - POST API trả dữ liệu

**Yêu cầu:** thêm route:

```text
POST /api/random-quote
```

Trả JSON:

```json
{"quote":"Practice makes progress.","author":"Demo"}
```

**Đáp án gợi ý:**

```python
@app.post("/api/random-quote")
def random_quote():
    return {"quote": "Practice makes progress.", "author": "Demo"}
```

### Bài tập nhỏ 10.3 - Jinja2 template

**Yêu cầu:** render HTML từ Jinja2 template, truyền biến `app_name` và `max_items`.

**Đáp án gợi ý:**

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": "My App", "max_items": 5},
    )
```

`templates/index.html`:

```html
<h1>{{ app_name }}</h1>
<p>Max items: {{ max_items }}</p>
```

### Bài tập nhỏ 10.4 - HTML có button gọi API bằng fetch()

**Yêu cầu:** tạo HTML có button, bấm button gọi `/api/random-quote` bằng `fetch()` và render kết quả.

**Đáp án gợi ý phần JS:**

```html
<button id="btn" type="button">Get Quote</button>
<div id="result"></div>
<script>
function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.getElementById("btn").addEventListener("click", async () => {
    const result = document.getElementById("result");
    result.textContent = "Loading...";
    try {
        const response = await fetch("/api/random-quote", { method: "POST" });
        if (!response.ok) throw new Error("API error");
        const data = await response.json();
        result.innerHTML = `<p>${escapeHtml(data.quote)} — ${escapeHtml(data.author)}</p>`;
    } catch (error) {
        result.textContent = "Lỗi: " + error.message;
    }
});
</script>
```

**Liên hệ dự án:** mở `app/templates/index.html`. Logic JavaScript tương tự: button → fetch POST → render items.

### Bài tập nhỏ 10.5 - Dùng Pydantic response model

**Yêu cầu:** tạo Pydantic model `QuoteResponse` và khai báo `response_model=QuoteResponse`.

**Đáp án gợi ý:**

```python
from pydantic import BaseModel

class QuoteResponse(BaseModel):
    quote: str
    author: str

@app.post("/api/random-quote", response_model=QuoteResponse)
def random_quote():
    return QuoteResponse(quote="Practice makes progress.", author="Demo")
```

### Bài tập nhỏ 10.6 - HTTPException

**Yêu cầu:** nếu không có dữ liệu, trả lỗi 500 thay vì crash.

**Đáp án gợi ý:**

```python
from fastapi import HTTPException

@app.post("/api/data")
def get_data():
    data = []  # Giả sử không có dữ liệu
    if not data:
        raise HTTPException(status_code=502, detail="No data available")
    return {"items": data}
```

**Liên hệ dự án:** mở `app/main.py` dòng 49 và 54. Dự án raise `HTTPException(502)` khi không crawl được và `HTTPException(500)` khi model lỗi.

### Bài cuối chặng 10 - Code lại web demo mini giống dự án

**Bối cảnh:** đây là bản nhỏ của `app/main.py` và `app/templates/index.html`.

**Thư mục tự tạo:** `quote_app/`.

**Cấu trúc cần có:**

```text
quote_app/
├── __init__.py
├── main.py
├── quotes.jsonl
└── templates/index.html
```

**Yêu cầu cụ thể:**

1. `quotes.jsonl` có ít nhất 5 dòng, mỗi dòng:

```json
{"quote":"...","author":"..."}
```

2. `main.py`:
   - Tạo FastAPI app.
   - Mount Jinja2 templates.
   - `GET /` trả HTML, truyền `app_name` vào template.
   - `GET /healthz` trả `{"status":"ok","version":"0.1.0"}`.
   - `POST /api/random-quote` đọc quote ngẫu nhiên từ JSONL và trả `QuoteResponse`.
   - Nếu file rỗng hoặc lỗi, raise `HTTPException(status_code=500, detail="...")`.
3. `index.html`:
   - Hiển thị `{{ app_name }}`.
   - Có button.
   - Có vùng result.
   - Bấm button gọi API, không reload page.
   - Escape HTML output.
   - Nếu API lỗi, hiển thị message lỗi.
4. Chạy:

```bash
uvicorn quote_app.main:app --reload
```

**Kết quả đúng:**

- Mở browser thấy trang có button.
- Bấm button thấy quote hiện ra.
- `/healthz` trả JSON ok.
- API lỗi không làm browser trắng trang.

**Liên hệ dự án thật:** sau bài này, thay `random quote` bằng:

- `crawl_articles(mode="demo", limit=MAX_ARTICLES_PER_DEMO)`.
- `ViT5Summarizer.summarize_batch(content_texts)`.
- Trả list `SummaryItem` cho frontend.

**So sánh dự án:** mở `app/main.py` và `app/templates/index.html`.

Checklist qua chặng:

- Bạn tự viết được FastAPI route cơ bản.
- Bạn biết render Jinja2 template với biến.
- Bạn biết frontend gọi POST API bằng `fetch()`.
- Bạn hiểu `escapeHtml()` dùng để chống XSS.
- Bạn hiểu luồng `button → API → crawler → model → response → render`.

---

## Chặng 11 - Test, Debug, Docker Và Chạy Dự Án Như Một Sản Phẩm

**Mục tiêu:** biết kiểm tra dự án chạy đúng, debug lỗi phổ biến, và giải thích project khi đưa vào CV/phỏng vấn.

### Bạn cần hiểu gì?

- **Unit test** kiểm tra function nhỏ, ví dụ `canonicalize_url()`, `parse_label_json()`.
- **Integration test** kiểm tra cả pipeline nhỏ, ví dụ JSONL input → split output.
- **pytest** là test runner phổ biến. Chạy bằng `python -m pytest`.
- `.gitignore` có thể làm file data không hiện trong Git, nhưng file vẫn tồn tại trên máy.
- Lỗi path Windows/Linux thường do dùng `\` và `/` lẫn lộn; `Path` giúp giảm lỗi.
- Lỗi encoding thường do đọc/ghi không dùng UTF-8.
- Docker image là gói app; container là app đang chạy từ image.
- `.env` chứa cấu hình như `HF_MODEL_ID`, `GEMINI_API_KEYS`, limit demo.
- Dự án cấu hình test trong `pyproject.toml`: `testpaths = ["tests_simple"]`, `pythonpath = ["."]`.

### File trong dự án

- `pyproject.toml` → `[tool.pytest.ini_options]`: cấu hình pytest.
- `.gitignore`: bỏ qua data/model local.
- `README.md`: hướng dẫn chạy dự án.
- `Dockerfile`, `docker-compose.yml`: chạy FastAPI bằng Docker.

### Bài tập nhỏ 11.1 - Test canonical URL

**Yêu cầu:** viết test chứng minh `utm_source` bị bỏ.

**Đáp án gợi ý:**

```python
def test_canonicalize_url_removes_tracking():
    url = "https://a.com/news?id=1&utm_source=fb#top"
    assert canonicalize_url(url) == "https://a.com/news?id=1"
```

### Bài tập nhỏ 11.2 - Test parser confidence

**Yêu cầu:** test `confidence=8` thành `1.0`.

**Đáp án gợi ý:**

```python
def test_parse_label_json_clamps_confidence():
    parsed = parse_label_json('{"summary":"abc", "confidence": 8}')
    assert parsed.confidence == 1.0
```

### Bài tập nhỏ 11.3 - Test split output files

**Yêu cầu:** tạo 10 row fake, gọi function split, kiểm tra 3 file tồn tại và tổng dòng đúng.

**Đáp án gợi ý:**

```python
def test_export_splits_creates_files(tmp_path):
    rows = [
        {
            "article_id": i,
            "source": "demo",
            "url": f"https://example.com/{i}",
            "title": f"Title {i}",
            "content_text": "Some content text here",
            "summary": "Some summary here",
            "prompt_version": "v1",
            "qc_passed": True,
        }
        for i in range(10)
    ]
    # Write input
    input_path = tmp_path / "labeled.jsonl"
    write_jsonl(input_path, rows)
    # Export
    counts = export_splits(input_path, tmp_path / "output")
    assert (tmp_path / "output" / "train.jsonl").exists()
    assert (tmp_path / "output" / "val.jsonl").exists()
    assert (tmp_path / "output" / "test.jsonl").exists()
    assert sum(counts.values()) == 10
```

### Bài tập nhỏ 11.4 - Debug file bị ignore

**Yêu cầu:** tạo `data/raw/test.jsonl`, chạy `git status`, giải thích vì sao không thấy file nếu `.gitignore` đang ignore `data/`.

**Kết quả đúng:** bạn hiểu file vẫn tồn tại trên máy, chỉ là Git không track.

### Bài tập nhỏ 11.5 - Docker command cơ bản

**Yêu cầu:** chạy:

```bash
docker compose up --build
```

Sau đó mở:

```text
http://localhost:8000/healthz
```

**Kết quả đúng:** thấy `{"status":"ok"}` nếu env/model không chặn app khởi động.

### Bài cuối chặng 11 - Viết test và checklist chạy dự án thật

**Bối cảnh:** sau khi code được dự án, bạn cần chứng minh nó chạy đúng và biết giải thích khi có lỗi.

**Yêu cầu cụ thể:**

1. Tạo hoặc cập nhật test cho 3 nhóm:
   - URL tools: `canonicalize_url`, `url_hash`.
   - Label parser: JSON hợp lệ, confidence clamp, refusal.
   - Split dataset: input fake → output train/val/test.
2. Tạo file ghi chú `docs/run_checklist.md` hoặc ghi vào notebook cá nhân:
   - Cách tạo env.
   - Cách crawl thử 10 bài.
   - Cách label (AI Studio key + fake LLM).
   - Cách split dataset.
   - Cách chạy notebook.
   - Cách chạy web.
   - Cách chạy Docker.
3. Chạy các command thật:

```bash
# Crawl thử
python -m app.crawler --mode labeling --source vnexpress --limit 10 --output data/raw/articles.jsonl --verbose

# Label (cần GEMINI_API_KEYS hoặc dùng fake LLM)
python -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl --limit 3

# Split
python -m labeling.split_dataset --input data/labeled/labeled_articles.jsonl --output data/datasets/v2

# Web demo
uvicorn app.main:app --reload

# Test (nếu có tests_simple/)
python -m pytest
```

4. Với mỗi command, ghi lại:
   - Command.
   - Kết quả đúng mong đợi.
   - Lỗi thường gặp.
   - Cách xử lý.

**Kết quả đúng:**

- Bạn biết command nào dùng cho crawl labeling, command nào dùng cho web demo.
- Bạn biết file data bị `.gitignore` vẫn có thể mở trong máy.
- Bạn biết live crawl không thể tái tạo y hệt report lịch sử.
- Bạn có thể trình bày project trong 3-5 phút.

Checklist qua chặng:

- Bạn viết được test đơn giản cho pure function.
- Bạn biết chạy FastAPI và Docker.
- Bạn có checklist để tự debug thay vì chỉ nhìn terminal đứng im.

---

## Lịch Học Gợi Ý 8 Tuần

| Tuần | Chặng | Kết quả cần đạt |
|---|---:|---|
| Tuần 1 | 0-1 | Code lại helper JSONL, schema, source config. Hiểu env var, package. |
| Tuần 2 | 2-3 | Code RSS fetch, canonical URL, hash, rate limiter, robots. Hiểu async cơ bản. |
| Tuần 3 | 4-5 | Code extractor (trafilatura + fallback), SimHash, mini crawler xuất JSONL. |
| Tuần 4 | 6 | Code prompt/parser/fake labeling pipeline. Hiểu AI Studio, key rotation, model fallback. |
| Tuần 5 | 7 | Code QC (fuzzy matching, number/entity check) và split train/val/test. |
| Tuần 6 | 8 | Chạy notebook mini fine-tune flow, hiểu ViT5 + LoRA + ROUGE. |
| Tuần 7 | 9 | Code inference class, hiểu lazy loading, PEFT adapter loading, batch summarize. |
| Tuần 8 | 10-11 | Code FastAPI web demo, Docker, tests, checklist chạy dự án. |

Nếu mỗi ngày chỉ có 1-2 giờ, có thể chia mỗi chặng thành 3 buổi:

1. Buổi 1: đọc lý thuyết và làm bài nhỏ.
2. Buổi 2: làm bài cuối chặng.
3. Buổi 3: so sánh với code dự án và viết ghi chú phỏng vấn.

## Thứ Tự Code Lại Dự Án Thật

Sau khi làm xong bài tập practice, bạn có thể tự code lại repo theo thứ tự này:

1. `app/schemas.py` — kiểu dữ liệu dùng chung.
2. `app/sources.py` — cấu hình nguồn báo.
3. Các helper JSONL trong `labeling/label_dataset.py`, `labeling/split_dataset.py`.
4. `app/crawler.py` phần URL tools: `canonicalize_url`, `url_hash`.
5. `app/crawler.py` phần RSS: `fetch_feed`, `_to_utc`, `_category_from_url`.
6. `app/crawler.py` phần extract: `normalize_text`, `word_count`, `extract_from_html`.
7. `app/crawler.py` phần dedupe: `simhash64`, `hamming`.
8. `app/crawler.py` phần pipeline: `crawl_articles`, `write_jsonl`, CLI.
9. `labeling/prompt.py` — prompt, template, parser.
10. `labeling/gemini_labeler.py` — AI Studio client, key rotation, model fallback.
11. `labeling/vertex_labeler.py` — legacy Vertex AI client (nếu cần).
12. `labeling/label_dataset.py` — pipeline label nhiều bài async.
13. `labeling/qc.py` — QC checks (word count, sentence count, number faithfulness, entity faithfulness + fuzzy).
14. `labeling/split_dataset.py` — split deterministic.
15. `notebooks/finetune_vit5_lora.ipynb` — fine-tune flow.
16. `app/summarizer.py` — inference class, lazy load, PEFT adapter, batch summarize.
17. `app/main.py` — FastAPI routes, integrate crawler + summarizer.
18. `app/templates/index.html` — frontend, fetch API, escapeHtml.
19. `Dockerfile`, `docker-compose.yml` — containerize.

## Acceptance Criteria Cuối Lộ Trình

Bạn hoàn thành lộ trình khi tự làm được các việc sau mà không cần copy code:

- Tự code crawler tạo được `data/raw/articles.jsonl`.
- Tự giải thích được vì sao crawler dùng RSS-first, canonical URL, robots/rate limit, dedupe (URL + SimHash).
- Tự code labeling pipeline dùng AI Studio (GeminiLabeler) hoặc fake LLM.
- Tự giải thích được key rotation, model fallback, asyncio.to_thread, Semaphore.
- Tự giải thích được prompt version `1.2.0` và vì sao report labeling là artifact lịch sử.
- Tự code QC và split dataset ra `train.jsonl`, `val.jsonl`, `test.jsonl`.
- Tự chạy và giải thích notebook fine-tune ViT5 + LoRA.
- Tự load model bằng `ViT5Summarizer` hoặc class tương tự và summarize text mới.
- Tự chạy web demo tại `http://localhost:8000`.
- Tự chạy Docker bằng `docker compose up --build`.
- Tự trả lời trong phỏng vấn:
  - Vì sao dùng Gemini (AI Studio) để gán nhãn? Vì sao key rotation?
  - Vì sao dùng ViT5 cho tiếng Việt?
  - Vì sao dùng LoRA thay vì full fine-tune?
  - Vì sao dùng JSONL thay database?
  - Vì sao live crawl hôm nay không thể tạo lại y hệt dataset/report lịch sử?
  - SimHash dùng để làm gì? Hamming distance là gì?
  - asyncio.Semaphore, asyncio.to_thread, asyncio.gather dùng ở đâu trong dự án?

## Cách Tự Ghi Chú Sau Mỗi Chặng

Sau mỗi chặng, tạo một file ghi chú cá nhân, ví dụ `notes/chang_03.md`, trả lời 5 câu:

1. Chặng này học kỹ thuật gì?
2. Function quan trọng nhất là gì?
3. Input/output của function đó là gì?
4. Lỗi mình gặp là gì và sửa ra sao?
5. Nếu nhà tuyển dụng hỏi, mình giải thích trong 3 câu như thế nào?

Ví dụ trả lời ngắn cho chặng crawler:

```text
Chặng này học RSS crawler. Function quan trọng là fetch_feed(): input RSS URL, output list ArticleCandidate. Em dùng RSS để lấy danh sách bài trước, sau đó mới fetch HTML từng URL. Khi một nguồn lỗi, crawler bỏ qua nguồn đó và tiếp tục nguồn khác để pipeline không crash.
```

## Command Thực Tế Nên Nhớ

Crawl thử ít bài:

```bash
python -m app.crawler --mode labeling --source vnexpress --limit 10 --output data/raw/articles.jsonl --verbose
```

Label dataset (AI Studio - mặc định):

```bash
export GEMINI_API_KEYS=key1,key2,key3
python -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl --concurrency 5
```

Label dataset (Vertex AI - legacy):

```bash
python -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl --backend vertex
```

Split dataset:

```bash
python -m labeling.split_dataset --input data/labeled/labeled_articles.jsonl --output data/datasets/v2
```

Chạy web:

```bash
uvicorn app.main:app --reload
```

Chạy Docker:

```bash
docker compose up --build
```

Chạy test:

```bash
python -m pytest
```

Chạy lint:

```bash
ruff check app/ labeling/
```
