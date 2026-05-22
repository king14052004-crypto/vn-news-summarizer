# Lộ Trình Học Để Tự Code Lại `vn-news-summarizer`

Tài liệu này dành cho người mới học, chưa cần biết trước cấu trúc dự án. Mục tiêu không phải là học thuộc code hiện có, mà là hiểu từng mảnh nhỏ rồi tự code lại được toàn bộ pipeline: crawl tin tức, tạo nhãn bằng Vertex/Gemini, kiểm tra chất lượng dữ liệu, chia dataset, fine-tune ViT5 + LoRA, load model để inference, và chạy web demo bằng FastAPI.

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
│   ├── vertex_labeler.py        # Gọi Vertex AI Gemini
│   ├── label_dataset.py         # Đọc bài raw, gọi labeler, ghi JSONL
│   ├── qc.py                    # Kiểm tra chất lượng summary
│   └── split_dataset.py         # Chia train/val/test
├── notebooks/finetune_vit5_lora.ipynb
├── data/                        # Dữ liệu local, thường bị .gitignore
├── docs/                        # Report và tài liệu học
├── tests_simple/                # Test đơn giản cho artifact/pipeline
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

---

## Chặng 0 - Nền Tảng Python Cho Dự Án

**Mục tiêu:** hiểu cách một project Python được chia thành nhiều file, biết đọc/ghi dữ liệu JSONL, biết chạy file bằng command line.

### Bạn cần hiểu gì?

- `module` là một file Python, ví dụ `crawler.py`.
- `package` là một thư mục có `__init__.py`, ví dụ `app/`, `labeling/`.
- `import` giúp dùng code từ file khác.
- `python -m app.crawler` nghĩa là chạy module `crawler.py` nằm trong package `app`.
- JSON là một object/list dữ liệu.
- JSONL là nhiều dòng JSON, mỗi dòng là một record riêng.
- `Path` giúp code chạy ổn hơn trên Windows/Linux.
- `argparse` giúp tạo command như `--input`, `--output`, `--limit`.

### File/function trong dự án

- `app/schemas.py`: định nghĩa object dữ liệu dùng giữa crawler, API, summarizer.
- `labeling/split_dataset.py`: có helper `read_jsonl()`, `write_jsonl()`, CLI.
- `app/crawler.py`: có `_build_parser()`, `_run_cli()`, `main()` để chạy crawler bằng command.

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

### Bài cuối chặng 0 - Code lại helper JSONL cho dự án

**Bối cảnh:** dự án cần lưu bài báo, nhãn, dataset bằng JSONL vì dễ đọc, dễ append, không cần database.

**File tự tạo:** `practice_jsonl.py`.

**Yêu cầu cụ thể:**

1. Viết `write_jsonl(path, rows)`:
   - `path` có thể là string hoặc `Path`.
   - `rows` là list dict.
   - Tự tạo thư mục cha nếu chưa tồn tại.
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

**Kết quả đúng:**

```bash
python practice_jsonl.py
# 3
```

Checklist qua chặng:

- Bạn giải thích được JSONL là gì.
- Bạn biết vì sao dataset dùng JSONL thay vì database.
- Bạn tự viết được `read_jsonl()` và `write_jsonl()`.
- Bạn chạy được file bằng `python file.py`.

---

## Chặng 1 - Data Schema Và Source Config

**Mục tiêu:** hiểu dữ liệu đi qua pipeline có hình dạng gì và vì sao cần cấu hình nguồn báo rõ ràng.

### Bạn cần hiểu gì?

- Nếu truyền dict lung tung, rất dễ sai key như `content`, `content_text`, `article_text`.
- `dataclass` giúp gom dữ liệu thành object rõ field.
- `frozen=True` làm object khó bị sửa nhầm sau khi tạo.
- `str | None` nghĩa là field có thể là chuỗi hoặc không có giá trị.
- Source config giúp crawler biết báo nào enabled, RSS URL nào cần đọc, domain nào hợp lệ.

### File/function trong dự án

- `app/schemas.py`
  - `ArticleCandidate`: bài báo mới lấy từ RSS, chưa fetch HTML.
  - `CrawledArticle`: bài báo đã có `content_text`.
  - `SummaryItem`: response item trả về web/API.
- `app/sources.py`
  - `NewsSource`: cấu hình một nguồn tin.
  - `SOURCES`: danh sách nguồn chuẩn.
  - `enabled_sources()`: lọc nguồn đang bật.
  - `canonical_category()`: chuẩn hóa category.

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

### Bài tập nhỏ 1.3 - Source config đơn giản

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

### Bài tập nhỏ 1.4 - Chuẩn hóa category

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

### Bài cuối chặng 1 - Code lại schema và source config kiểu dự án

**Bối cảnh:** crawler cần 2 kiểu dữ liệu:

- Bài mới lấy từ RSS: có title, url, source, category, published date.
- Bài đã extract: có thêm `content_text`, `article_id`, `word_count`.

**File tự tạo:** `practice_project_schema.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `ArticleCandidate`:
   - `source: str`
   - `title: str`
   - `url: str`
   - `category: str | None = None`
   - `published_at: str | None = None`
2. Tạo dataclass `CrawledArticle`:
   - `article_id: str`
   - `source: str`
   - `url: str`
   - `title: str`
   - `content_text: str`
   - `category: str | None = None`
   - `published_at: str | None = None`
   - `word_count: int = 0`
3. Tạo dataclass `NewsSource`:
   - `id`, `name`, `domains`, `rss_feeds`, `enabled`, `max_items_per_feed`.
4. Tạo 3 nguồn fake, trong đó 1 nguồn disabled.
5. Viết `enabled_sources(only=None)`.
6. Viết `canonical_category(raw)`.

**Tự kiểm tra:**

```python
sources = enabled_sources()
assert len(sources) == 2
assert canonical_category("Xa hoi") == "xa-hoi"
candidate = ArticleCandidate(source="demo", title="Tin A", url="https://example.com/a")
assert candidate.title == "Tin A"
```

Checklist qua chặng:

- Bạn hiểu khác nhau giữa dataclass và Pydantic model.
- Bạn biết một article đi từ RSS sang extracted article như thế nào.
- Bạn tự code được cấu hình source không phụ thuộc database.

---

## Chặng 2 - HTTP, RSS Và CLI Crawler Tối Giản

**Mục tiêu:** đọc được RSS feed, lấy ra danh sách bài báo gồm title và URL, chưa cần extract nội dung.

### Bạn cần hiểu gì?

- HTTP request là gửi yêu cầu tới URL và nhận response.
- RSS là XML, thường có nhiều item, mỗi item có `title`, `link`, `published`.
- `httpx.AsyncClient` giúp gọi HTTP async.
- `async def` tạo coroutine, cần `await` để chờ kết quả.
- `feedparser.parse()` biến XML RSS thành object Python dễ đọc.
- CLI giúp chạy crawler bằng command thay vì sửa code.

### File/function trong dự án

- `app/crawler.py`
  - `PoliteClient`: client HTTP có timeout/rate limit/retry.
  - `fetch_feed()`: lấy RSS và parse ra `ArticleCandidate`.
  - `_to_utc()`: chuẩn hóa ngày tháng.
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

**Yêu cầu:** tạo `practice_rss_parse.py`, dùng `feedparser.parse(xml_text)` và in 5 title đầu.

**Đáp án gợi ý:**

```python
import feedparser

feed = feedparser.parse(xml_text)
for entry in feed.entries[:5]:
    print(entry.get("title"), entry.get("link"))
```

**Kết quả đúng:** mỗi dòng có title và link bài viết.

### Bài tập nhỏ 2.4 - CLI nhận URL RSS

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

1. Tạo dataclass `ArticleCandidate` gồm `source`, `title`, `url`, `category`, `published_at`.
2. Viết async function `fetch_feed(source_id, rss_url, limit)`:
   - Request RSS bằng `httpx.AsyncClient`.
   - Parse bằng `feedparser`.
   - Trả list `ArticleCandidate`.
   - Nếu feed lỗi, không crash, trả list rỗng.
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

Checklist qua chặng:

- Bạn giải thích được RSS dùng để làm gì.
- Bạn biết `async/await` ở mức đủ dùng.
- Bạn tự code được function lấy article candidate từ RSS.
- Bạn chạy được CLI có `--url` và `--limit`.

---

## Chặng 3 - URL Cleanup, Robots Và Rate Limit

**Mục tiêu:** biến crawler từ "request được" thành crawler có trách nhiệm: không crawl trùng, không spam server, biết tôn trọng robots.txt.

### Bạn cần hiểu gì?

- Một URL có các phần: scheme (`https`), domain, path, query, fragment.
- Query tracking như `utm_source`, `utm_medium`, `fbclid` không làm thay đổi nội dung bài báo.
- Canonical URL là URL đã được làm sạch để so sánh/dedupe.
- `robots.txt` là file website dùng để nói crawler được/không được crawl path nào.
- Rate limit giúp cùng một host không bị request quá nhanh.
- Retry dùng khi gặp lỗi tạm thời như `429`, `500`, `502`, `503`.

### File/function trong dự án

- `app/crawler.py`
  - `canonicalize_url(url)`: bỏ tracking params, fragment, sort query.
  - `url_hash(url)`: tạo ID ổn định từ URL.
  - `RobotsCache`: cache robots.txt theo host.
  - `PoliteClient.get()`: request HTTP có timeout, retry, rate limit.

### Bài tập nhỏ 3.1 - Tách thành phần URL

**Yêu cầu:** dùng `urllib.parse.urlsplit()` để in `scheme`, `netloc`, `path`, `query`, `fragment` của URL:

```text
https://example.com/news/a?id=1&utm_source=fb#comment
```

**Đáp án gợi ý:**

```python
from urllib.parse import urlsplit

parts = urlsplit("https://example.com/news/a?id=1&utm_source=fb#comment")
print(parts.scheme)
print(parts.netloc)
print(parts.path)
print(parts.query)
print(parts.fragment)
```

**Kết quả đúng:**

```text
https
example.com
/news/a
id=1&utm_source=fb
comment
```

### Bài tập nhỏ 3.2 - Canonical URL

**Yêu cầu:** viết `canonicalize_url(url)`:

- Bỏ fragment `#...`.
- Bỏ query key bắt đầu bằng `utm_`.
- Bỏ `fbclid`, `gclid`.
- Sort query params theo key.
- Bỏ dấu `/` cuối path, trừ khi path chỉ là `/`.

**Đáp án gợi ý:**

```python
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_KEYS = {"fbclid", "gclid"}

def canonicalize_url(url):
    parts = urlsplit(url.strip())
    query_items = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key.startswith("utm_") or lower_key in TRACKING_KEYS:
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

### Bài tập nhỏ 3.4 - Rate limiter đơn giản

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

Checklist qua chặng:

- Bạn biết URL canonical dùng để làm gì.
- Bạn biết vì sao cần rate limit.
- Bạn tự code được hash ổn định cho article ID.
- Bạn hiểu ý tưởng chính của `PoliteClient` trong dự án.

---

## Chặng 4 - Extract Nội Dung Bài Báo Từ HTML

**Mục tiêu:** từ HTML nhiều menu/quảng cáo/footer lấy ra phần nội dung bài báo sạch trong `content_text`.

### Bạn cần hiểu gì?

- HTML của một trang báo không chỉ có nội dung bài viết, còn có menu, script, quảng cáo, bài liên quan.
- Model summarization cần text sạch, không cần HTML tag.
- `trafilatura.extract()` là thư viện chuyên lấy nội dung chính từ trang web.
- `readability-lxml` và `BeautifulSoup` có thể dùng làm fallback.
- Normalize text giúp bỏ khoảng trắng thừa, chuẩn hóa Unicode, giảm noise.
- Crawler nên bỏ bài quá ngắn vì không đủ thông tin để summarize/label.

### File/function trong dự án

- `app/crawler.py`
  - `ExtractedArticle`: object chứa kết quả extract.
  - `normalize_text(text)`: làm sạch whitespace và Unicode.
  - `word_count(text)`: đếm số từ.
  - `extract_from_html(html, url)`: lấy title/content/date bằng trafilatura, fallback readability.

### Bài tập nhỏ 4.1 - Lấy text từ HTML đơn giản

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

### Bài tập nhỏ 4.2 - Fallback lấy toàn bộ paragraph

**Yêu cầu:** nếu HTML không có `<article>`, lấy text từ tất cả thẻ `<p>`.

**Đáp án gợi ý:**

```python
def extract_text_basic(html):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if article:
        return article.get_text(" ", strip=True)
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return " ".join(p for p in paragraphs if p)
```

### Bài tập nhỏ 4.3 - Normalize text

**Yêu cầu:** viết `normalize_text(text)`:

- Nếu `None` hoặc chuỗi rỗng thì trả `""`.
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
```

### Bài tập nhỏ 4.4 - Bỏ bài quá ngắn

**Yêu cầu:** viết `word_count(text)` và nếu text dưới 50 từ thì return `None`.

**Đáp án gợi ý:**

```python
def word_count(text):
    return len([w for w in text.split() if w.strip()])

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
   - `published_at: str | None = None`
2. Viết `normalize_text(text)`.
3. Viết `word_count(text)`.
4. Viết `extract_from_html(html, min_words=50)`:
   - Nếu input rỗng, return `None`.
   - Ưu tiên lấy text trong `<article>`.
   - Nếu không có `<article>`, lấy tất cả `<p>`.
   - Lấy title từ `<h1>` nếu có.
   - Normalize text.
   - Nếu dưới `min_words`, return `None`.
   - Nếu đạt, return `ExtractedArticle`.
5. Tạo file HTML test `sample_article.html` và đọc vào để test.

**Command tự kiểm tra:**

```bash
python practice_extract.py sample_article.html
```

**Kết quả đúng:**

- HTML có `<article>`: không lấy menu/footer.
- HTML không có `<article>`: vẫn lấy được paragraph.
- HTML quá ngắn: in `None` hoặc message `too short`.
- Output cuối có `title`, `word_count`, đoạn đầu của `content_text`.

Checklist qua chặng:

- Bạn phân biệt được HTML và article text.
- Bạn tự code được extractor đơn giản.
- Bạn hiểu vì sao dự án dùng trafilatura trước rồi fallback.

---

## Chặng 5 - Dedupe Và Crawl Pipeline Hoàn Chỉnh

**Mục tiêu:** ghép các phần đã học thành crawler tạo được JSONL bài báo: discover RSS -> lọc URL -> fetch HTML -> extract text -> dedupe -> save.

### Bạn cần hiểu gì?

- Pipeline là chuỗi nhiều bước, mỗi bước nhận input và tạo output cho bước sau.
- Dedupe URL dùng set/hash để bỏ bài trùng link.
- Dedupe content dùng SimHash để bỏ nội dung gần trùng.
- Hamming distance đo số bit khác nhau giữa hai hash.
- Crawl stats giúp biết crawler đang làm gì: discovered, fetched, extracted, skipped.
- `--limit` nên là limit tổng số bài output, không phải limit số RSS item đọc.

### File/function trong dự án

- `app/crawler.py`
  - `simhash64(text)`: tạo fingerprint nội dung.
  - `hamming(a, b)`: so sánh 2 simhash.
  - `crawl_articles(...)`: pipeline crawl chính.
  - `write_jsonl(...)`: ghi output.
  - `_run_cli(...)`: command `python -m app.crawler ...`.

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

### Bài tập nhỏ 5.2 - Stats object

**Yêu cầu:** tạo dataclass `CrawlStats` có `discovered`, `fetched`, `extracted`, `fetch_failed`, `extract_failed`, rồi tăng số trong pipeline giả.

**Đáp án gợi ý:**

```python
from dataclasses import dataclass

@dataclass
class CrawlStats:
    discovered: int = 0
    fetched: int = 0
    extracted: int = 0
    fetch_failed: int = 0
    extract_failed: int = 0
```

### Bài tập nhỏ 5.3 - Pipeline giả không dùng internet

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

### Bài tập nhỏ 5.4 - Ghi crawler output JSONL

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
   - `extract_from_html()`.
   - `write_jsonl()`.
3. Pipeline:
   - Đọc RSS.
   - Duyệt từng candidate.
   - Bỏ URL trùng.
   - Fetch HTML.
   - Extract text.
   - Bỏ bài dưới 50 từ.
   - Ghi JSONL khi đủ `limit` bài.
4. Mỗi record output cần có:
   - `article_id`
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

Checklist qua chặng:

- Bạn tự ghép được crawler từ các function nhỏ.
- Bạn hiểu vì sao live crawl không thể ra đúng lại dataset lịch sử.
- Bạn biết debug khi crawler chạy lâu: bật `--verbose`, giảm `--limit`, crawl từng source.
- Bạn đã đủ nền để đọc gần như toàn bộ `app/crawler.py`.

---

## Chặng 6 - Prompt, JSON Parser Và Vertex Labeling

**Mục tiêu:** hiểu cách dùng Gemini trên Vertex AI làm teacher model để tạo summary label cho dataset train ViT5.

### Bạn cần hiểu gì?

- Trong dự án này, Gemini không phải model chạy web demo cuối cùng.
- Gemini đóng vai trò **teacher**: đọc bài báo và tạo summary chất lượng cao.
- ViT5 đóng vai trò **student**: học lại từ dataset đã được Gemini gán nhãn.
- Prompt cần rõ schema output để parser đọc được.
- LLM có thể trả JSON lỗi, thiếu field, `confidence` quá lớn, hoặc refusal.
- Parser phải robust để pipeline không chết vì một output lỗi.
- Gọi nhiều bài cùng lúc cần giới hạn concurrency để không vượt quota.

### File/function trong dự án

- `labeling/prompt.py`
  - `SYSTEM_PROMPT`: vai trò và quy tắc cho Gemini.
  - `USER_TEMPLATE`: template chứa title/content bài báo.
  - `render_user_prompt(...)`: ghép dữ liệu article vào prompt.
  - `parse_label_json(...)`: parse JSON output robust.
- `labeling/vertex_labeler.py`
  - `VertexLabeler.generate(...)`: gọi Vertex AI Gemini.
- `labeling/label_dataset.py`
  - `_label_one(...)`: label một article.
  - `label_rows(...)`: label nhiều article.

### Bài tập nhỏ 6.1 - Render prompt từ template

**Yêu cầu:** viết function `render_prompt(title, content)` trả về prompt có format:

```text
Title: <title>
Content:
<content>

Return JSON with fields: summary, key_entities, confidence.
```

**Đáp án gợi ý:**

```python
def render_prompt(title, content):
    return (
        f"Title: {title}\n"
        f"Content:\n{content}\n\n"
        "Return JSON with fields: summary, key_entities, confidence."
    )
```

**Kết quả đúng:** prompt có title, content, và yêu cầu JSON.

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

1. JSON hợp lệ có summary và confidence.
2. `confidence=8` thì clamp về `1.0`.
3. `summary=null` và có `refusal_reason` thì summary thành `""`, refusal hợp lệ.
4. JSON nằm trong markdown fence ```json ... ``` vẫn parse được.
5. JSON lỗi thì raise `ValueError` ngắn gọn.

**Đáp án gợi ý:**

```python
import json
import re
from dataclasses import dataclass

@dataclass
class LabelOutput:
    summary: str
    key_entities: list[str]
    confidence: float
    refusal_reason: str | None = None

def strip_json_fence(raw):
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    return match.group(1).strip() if match else raw

def parse_label_json(raw):
    try:
        data = json.loads(strip_json_fence(raw))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json: {exc}") from exc

    summary = data.get("summary")
    refusal = data.get("refusal_reason")
    if summary is None and refusal:
        summary = ""
    if not isinstance(summary, str):
        raise ValueError("summary must be a string")

    confidence = float(data.get("confidence", 0.0))
    if confidence > 1:
        confidence = 1.0
    if confidence < 0:
        confidence = 0.0

    entities = data.get("key_entities") or []
    if not isinstance(entities, list):
        entities = []

    return LabelOutput(summary, [str(x) for x in entities], confidence, refusal)
```

**Kết quả đúng:**

```python
parsed = parse_label_json('{"summary": null, "confidence": 8, "refusal_reason": "too short"}')
assert parsed.summary == ""
assert parsed.confidence == 1.0
assert parsed.refusal_reason == "too short"
```

### Bài tập nhỏ 6.4 - Label JSONL bằng fake LLM

**Yêu cầu:** đọc `raw_articles.jsonl`, mỗi dòng có `title`, `content_text`. Với mỗi dòng:

- Render prompt.
- Gọi `fake_llm(prompt)`.
- Parse output.
- Ghi ra `labeled.jsonl` với các field cũ và thêm `summary`, `key_entities`, `confidence`, `prompt_version`.

**Kết quả đúng:** input 3 dòng tạo output 3 dòng, mỗi dòng có summary.

### Bài cuối chặng 6 - Code lại fake labeling pipeline kiểu dự án

**Bối cảnh:** trước khi gọi Vertex thật, bạn cần hiểu pipeline labeling bằng fake LLM để không bị rối bởi credential/quota.

**File tự tạo:** `practice_label_dataset.py`.

**Yêu cầu cụ thể:**

1. Tạo `PROMPT_VERSION = "practice_v1"`.
2. Tạo `render_user_prompt(title, content_text)`:
   - Nếu content dài hơn 6000 ký tự thì cắt còn 6000 ký tự.
   - Prompt phải yêu cầu output JSON.
3. Tạo dataclass `LabelOutput`.
4. Tạo `parse_label_json(raw)` robust theo bài 6.3.
5. Tạo async `fake_generate(prompt)`:
   - Return JSON string.
   - Summary có thể lấy 2 câu đầu từ prompt/content để giả lập.
6. Tạo `label_one(row)`:
   - Nhận dict article.
   - Gọi render prompt, fake generate, parse.
   - Return dict mới có thêm label fields.
7. Tạo `label_rows(rows, concurrency=3)`:
   - Dùng `asyncio.Semaphore`.
   - Label nhiều dòng.
8. Tạo CLI:

```bash
python practice_label_dataset.py --input data/practice/articles.jsonl --output data/practice/labeled.jsonl
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
  "prompt_version": "practice_v1"
}
```

**Kết quả đúng:**

- Nếu input có 5 dòng, output có 5 dòng.
- Dòng nào content rỗng thì vẫn không làm crash pipeline; có thể ghi `label_error`.
- Parser clamp `confidence > 1` về `1.0`.
- Bạn có thể giải thích sau này chỉ cần thay `fake_generate()` bằng `VertexLabeler.generate()`.

Checklist qua chặng:

- Bạn hiểu teacher-student learning ở mức dự án.
- Bạn tự viết được prompt renderer.
- Bạn tự viết được parser JSON robust.
- Bạn hiểu vì sao dự án cần `prompt_version`.

---

## Chặng 7 - QC Và Dataset Split

**Mục tiêu:** lọc summary kém chất lượng và chia dataset train/val/test ổn định.

### Bạn cần hiểu gì?

- Không phải label nào LLM tạo ra cũng nên đưa vào train.
- QC rule-based giúp bắt lỗi đơn giản, ví dụ summary quá ngắn/quá dài, có số không có trong bài gốc.
- Sentence count giúp summary đúng yêu cầu 2-4 câu.
- Number faithfulness: số trong summary phải xuất hiện trong article.
- Entity faithfulness: tên riêng trong summary nên có trong article.
- Split dataset cần deterministic: chạy lại vẫn ra cùng train/val/test.
- Dự án dùng artifact JSONL làm source of truth thay vì DB.

### File/function trong dự án

- `labeling/qc.py`
  - `run_qc(row)`: trả kết quả pass/fail và lý do.
  - `_contains_numeric(...)`: kiểm tra số.
  - `_contains_entity(...)`: kiểm tra entity.
- `labeling/split_dataset.py`
  - `split_bucket(article_id)`: quyết định train/val/test.
  - `dataset_record(row)`: giữ field cần cho training.
  - `split_rows(rows)`: chia rows.
  - `export_splits(...)`: ghi 3 file JSONL.

### Bài tập nhỏ 7.1 - Đếm từ và câu

**Yêu cầu:** viết:

- `word_count(text)`.
- `sentence_count(text)` tách câu theo `.`, `!`, `?`.

**Đáp án gợi ý:**

```python
import re

def word_count(text):
    return len(re.findall(r"\w+", text or ""))

def sentence_count(text):
    sentences = [s.strip() for s in re.split(r"[.!?]+", text or "") if s.strip()]
    return len(sentences)
```

**Kết quả đúng:** summary 2 câu trả `sentence_count == 2`.

### Bài tập nhỏ 7.2 - Check số trong summary

**Yêu cầu:** nếu summary có số `9999` nhưng content không có `9999`, QC fail.

**Đáp án gợi ý:**

```python
import re

def numbers(text):
    return set(re.findall(r"\d+(?:[.,]\d+)?", text or ""))

def numbers_supported(summary, content):
    return numbers(summary).issubset(numbers(content))
```

**Kết quả đúng:**

```python
assert numbers_supported("Có 10 người tham gia.", "Sự kiện có 10 người tham gia.")
assert not numbers_supported("Có 9999 người.", "Sự kiện có 10 người.")
```

### Bài tập nhỏ 7.3 - QC summary đơn giản

**Yêu cầu:** viết `run_simple_qc(row)`:

- Fail nếu có `refusal_reason`.
- Summary phải 10-50 từ.
- Summary có ít nhất 1 câu.
- Mọi số trong summary phải có trong content.
- Return `{"qc_passed": bool, "qc_errors": list[str]}`.

**Đáp án gợi ý:**

```python
def run_simple_qc(row):
    errors = []
    summary = row.get("summary") or ""
    content = row.get("content_text") or ""
    if row.get("refusal_reason"):
        errors.append("refusal")
    wc = word_count(summary)
    if wc < 10 or wc > 50:
        errors.append("word_count")
    if sentence_count(summary) < 1:
        errors.append("sentence_count")
    if not numbers_supported(summary, content):
        errors.append("unsupported_numbers")
    return {"qc_passed": not errors, "qc_errors": errors}
```

### Bài tập nhỏ 7.4 - Split deterministic

**Yêu cầu:** chia theo `article_id`:

- Nếu số cuối hash `% 10 == 0`: test.
- Nếu `% 10 == 1`: val.
- Còn lại: train.

**Đáp án gợi ý:**

```python
import hashlib

def split_bucket(article_id):
    digest = hashlib.sha256(article_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 10
    if bucket == 0:
        return "test"
    if bucket == 1:
        return "val"
    return "train"
```

**Kết quả đúng:** cùng một `article_id` gọi nhiều lần luôn trả cùng split.

### Bài tập nhỏ 7.5 - Dataset record

**Yêu cầu:** từ labeled row có nhiều field, chỉ giữ field dùng cho training:

- `article_id`
- `source`
- `url`
- `title`
- `category`
- `published_at`
- `content_text`
- `summary`
- `prompt_version`

**Đáp án gợi ý:**

```python
DATASET_FIELDS = [
    "article_id", "source", "url", "title", "category", "published_at",
    "content_text", "summary", "prompt_version",
]

def dataset_record(row):
    return {key: row.get(key) for key in DATASET_FIELDS}
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
   - Summary phải 10-90 từ.
   - Summary phải 1-4 câu.
   - Mọi số trong summary phải xuất hiện trong `content_text`.
4. Chỉ giữ row QC pass.
5. Chia train/val/test bằng hash `article_id`.
6. Ghi 3 file:

```text
data/practice/dataset/train.jsonl
data/practice/dataset/val.jsonl
data/practice/dataset/test.jsonl
```

7. Mỗi dòng chỉ giữ dataset fields ở bài 7.5.
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
- JSONL output không chứa field thừa như `confidence`, `qc_errors`, `label_error`.

Checklist qua chặng:

- Bạn giải thích được vì sao cần QC trước khi train.
- Bạn tự code được split deterministic.
- Bạn hiểu dataset v2 là artifact lịch sử, không bị live crawl ghi đè.

---

## Chặng 8 - Fine-tune ViT5 + LoRA

**Mục tiêu:** hiểu đủ để chạy notebook fine-tune, giải thích được trong CV/phỏng vấn, và biết report metric ROUGE đến từ đâu.

### Bạn cần hiểu gì?

- Summarization trong dự án là bài toán text-to-text: input là bài báo, output là summary.
- Tokenizer biến text thành token IDs để model đọc.
- `input_ids` là token của article.
- `attention_mask` đánh dấu token thật/padding.
- `labels` là token của summary.
- Seq2Seq model học sinh output sequence mới.
- LoRA chỉ train một số adapter nhỏ, giúp nhẹ hơn full fine-tune.
- ROUGE-1 đo overlap unigram, ROUGE-2 đo overlap bigram, ROUGE-L đo longest common subsequence.
- Hyperparameter cần nhớ: model, max lengths, batch size, gradient accumulation, learning rate, epoch, seed.

### File/report trong dự án

- `notebooks/finetune_vit5_lora.ipynb`
  - Notebook fine-tune chính.
  - Tham số được viết trực tiếp trong notebook để dễ show với nhà tuyển dụng.
- `docs/training_report.md`
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
    # thêm 4 dòng nữa
]
train_data = samples[:4]
val_data = samples[4:5]
test_data = samples[5:]
print(len(train_data), len(val_data), len(test_data))
```

**Kết quả đúng:** in `4 1 1`.

### Bài tập nhỏ 8.2 - Hiểu tokenizer output

**Yêu cầu:** dùng tokenizer bất kỳ từ Hugging Face, tokenize một câu, in `input_ids` và `attention_mask`.

**Đáp án gợi ý:**

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("VietAI/vit5-base")
encoded = tokenizer("Tóm tắt: Đây là một bài báo ngắn.", max_length=32, truncation=True)
print(encoded.keys())
print(encoded["input_ids"][:10])
print(encoded["attention_mask"][:10])
```

**Kết quả đúng:** thấy dict có `input_ids`, `attention_mask`.

### Bài tập nhỏ 8.3 - Tạo preprocessing function

**Yêu cầu:** viết function nhận batch có `content_text` và `summary`, trả tokenized input và labels.

**Đáp án gợi ý:**

```python
def preprocess(batch):
    inputs = ["Tóm tắt: " + text for text in batch["content_text"]]
    model_inputs = tokenizer(inputs, max_length=512, truncation=True)
    labels = tokenizer(text_target=batch["summary"], max_length=128, truncation=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs
```

### Bài tập nhỏ 8.4 - Đếm trainable parameters với LoRA

**Yêu cầu:** sau khi bọc model bằng PEFT LoRA, in số parameter trainable.

**Đáp án gợi ý:**

```python
def print_trainable_parameters(model):
    trainable = 0
    total = 0
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f"trainable={trainable} total={total} percent={100 * trainable / total:.2f}%")
```

**Kết quả đúng:** trainable nhỏ hơn total rất nhiều.

### Bài tập nhỏ 8.5 - Tính ROUGE cho 2 câu

**Yêu cầu:** dùng `rouge_score` tính ROUGE giữa prediction và reference.

**Đáp án gợi ý:**

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)
score = scorer.score("Hà Nội mưa lớn.", "Hà Nội có mưa lớn trong ngày.")
print(score["rouge1"].fmeasure)
print(score["rouge2"].fmeasure)
print(score["rougeL"].fmeasure)
```

### Bài cuối chặng 8 - Tạo notebook mini fine-tune flow

**Bối cảnh:** bạn chưa cần train ra metric đẹp. Mục tiêu là hiểu pipeline notebook từ dataset tới generate/eval.

**File tự tạo:** `notebooks/practice_finetune_flow.ipynb`.

**Yêu cầu cụ thể theo cell:**

1. **Cell 1 - Install/import**
   - Import `transformers`, `datasets`, `evaluate` hoặc `rouge_score`, `torch`.
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
   - Nếu dùng LoRA, cấu hình target module tương ứng.
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
- Có cell in trainable parameters nếu dùng LoRA.
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
- Với LoRA adapter, thường cần base model + adapter.
- Lazy loading nghĩa là chưa load model khi import file, chỉ load khi gọi summarize lần đầu.
- Batch inference giúp summarize nhiều bài cùng lúc hiệu quả hơn.
- Generation config ảnh hưởng output: `num_beams`, `max_new_tokens`, `no_repeat_ngram_size`, `length_penalty`.
- Web app không nên crash nếu input rỗng.

### File/function trong dự án

- `app/summarizer.py`
  - `GenerationConfig`: dataclass chứa tham số generate.
  - `ViT5Summarizer`: class load tokenizer/model.
  - `_ensure_loaded()`: lazy load model.
  - `summarize_batch(texts)`: generate nhiều summary.

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
- `summarize_batch(texts)` trả list cùng độ dài.

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

model_id = os.getenv("HF_MODEL_ID", "VietAI/vit5-base")
print(model_id)
```

### Bài tập nhỏ 9.4 - Generation config

**Yêu cầu:** tạo dataclass:

```python
@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 128
    num_beams: int = 4
    no_repeat_ngram_size: int = 3
```

Sau đó truyền config vào summarizer fake.

**Kết quả đúng:** bạn có thể đổi `max_new_tokens` khi tạo object.

### Bài cuối chặng 9 - Code lại summarizer class kiểu dự án

**Bối cảnh:** web demo cần một class duy nhất để nhận list text và trả list summary.

**File tự tạo:** `practice_inference.py`.

**Yêu cầu cụ thể:**

1. Tạo dataclass `GenerationConfig` gồm:
   - `max_new_tokens`
   - `num_beams`
   - `no_repeat_ngram_size`
   - `length_penalty`
2. Tạo class `SimpleSummarizer`:
   - `__init__(model_id=None, config=None)`.
   - Nếu `model_id` không truyền, đọc từ `HF_MODEL_ID`.
   - Có private fields `tokenizer`, `model`, `loaded`.
3. Viết `_ensure_loaded()`:
   - Nếu chưa loaded, load tokenizer/model bằng Hugging Face.
   - Nếu chưa muốn dùng model thật, cho phép `USE_FAKE_MODEL=1` để dùng fake summarizer.
   - Gọi nhiều lần không load lại.
4. Viết `summarize(text)`:
   - Text rỗng trả `""`.
   - Gọi `_ensure_loaded()`.
   - Generate summary.
5. Viết `summarize_batch(texts)`:
   - Return list cùng độ dài input.
   - Phần tử input rỗng trả `""`.
6. CLI test:

```bash
python practice_inference.py --text "Một đoạn tin tức dài..."
```

**Kết quả đúng:**

- `summarize("")` trả `""`.
- `summarize_batch(["a", "", "b"])` trả 3 phần tử.
- Log cho thấy model chỉ load một lần.
- Có thể đổi model bằng `HF_MODEL_ID`.

Checklist qua chặng:

- Bạn hiểu khác nhau giữa train và inference.
- Bạn biết lazy loading để web khởi động nhẹ hơn.
- Bạn tự code được interface giống `ViT5Summarizer`.

---

## Chặng 10 - FastAPI Web Demo Và Tích Hợp Toàn Bộ

**Mục tiêu:** ghép crawler và summarizer thành web app: mở trang, bấm nút, crawl tin mới, tóm tắt và hiển thị kết quả.

### Bạn cần hiểu gì?

- FastAPI route `GET /` trả trang HTML.
- FastAPI route `GET /healthz` dùng kiểm tra service sống.
- FastAPI route `POST /api/summarize-today` chạy logic chính.
- Pydantic response model giúp API output rõ schema.
- Jinja2 template render file HTML trong `templates/`.
- Frontend có thể gọi API bằng `fetch()` mà không reload page.
- `HTTPException` dùng để trả lỗi API rõ ràng.
- Environment variable giúp đổi cấu hình mà không sửa code.

### File/function trong dự án

- `app/main.py`
  - `index()`: render trang web.
  - `healthz()`: trả `{"status":"ok"}`.
  - `summarize_today()`: crawl demo và gọi summarizer.
- `app/templates/index.html`
  - Giao diện có button.
  - JavaScript gọi API.
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

### Bài tập nhỏ 10.2 - POST API trả quote

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

### Bài tập nhỏ 10.3 - HTML có button gọi API

**Yêu cầu:** tạo HTML có button, bấm button gọi `/api/random-quote` bằng `fetch()` và render quote.

**Đáp án gợi ý phần JS:**

```html
<script>
async function loadQuote() {
  const result = document.getElementById("result");
  result.textContent = "Loading...";
  try {
    const response = await fetch("/api/random-quote", { method: "POST" });
    if (!response.ok) throw new Error("API error");
    const data = await response.json();
    result.textContent = `${data.quote} - ${data.author}`;
  } catch (error) {
    result.textContent = "Không tải được dữ liệu.";
  }
}
</script>
```

### Bài tập nhỏ 10.4 - Dùng response model

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

### Bài cuối chặng 10 - Code lại web demo mini giống dự án

**Bối cảnh:** đây là bản nhỏ của `app/main.py` và `app/templates/index.html`.

**Thư mục tự tạo:** `quote_app/`.

**Cấu trúc cần có:**

```text
quote_app/
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
   - `GET /` trả HTML.
   - `GET /healthz` trả `{"status":"ok"}`.
   - `POST /api/random-quote` đọc quote từ JSONL và trả một quote.
   - Nếu file rỗng hoặc lỗi, raise `HTTPException(status_code=500, detail="...")`.
3. `index.html`:
   - Có button.
   - Có vùng result.
   - Bấm button gọi API, không reload page.
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

Checklist qua chặng:

- Bạn tự viết được FastAPI route cơ bản.
- Bạn biết frontend gọi POST API bằng `fetch()`.
- Bạn hiểu luồng `button -> API -> crawler -> model -> response -> render`.

---

## Chặng 11 - Test, Debug, Docker Và Chạy Dự Án Như Một Sản Phẩm

**Mục tiêu:** biết kiểm tra dự án chạy đúng, debug lỗi phổ biến, và giải thích project khi đưa vào CV/phỏng vấn.

### Bạn cần hiểu gì?

- Unit test kiểm tra function nhỏ, ví dụ `canonicalize_url()`.
- Integration test kiểm tra cả pipeline nhỏ, ví dụ JSONL input -> split output.
- `.gitignore` có thể làm file data không hiện trong Git, nhưng file vẫn tồn tại trên máy.
- Lỗi path Windows/Linux thường do dùng `\` và `/` lẫn lộn; `Path` giúp giảm lỗi.
- Lỗi encoding thường do đọc/ghi không dùng UTF-8.
- Docker image là gói app; container là app đang chạy từ image.
- `.env` chứa cấu hình như `HF_MODEL_ID`, credential, limit demo.

### File trong dự án

- `tests_simple/test_ground_truth.py`: kiểm tra số liệu report/dataset ground truth.
- `tests_simple/test_jsonl_pipeline.py`: kiểm tra JSONL pipeline đơn giản.
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

**Yêu cầu:** tạo 5 row fake, gọi function split, kiểm tra 3 file tồn tại.

**Đáp án gợi ý:**

```python
def test_export_splits_creates_files(tmp_path):
    rows = [
        {"article_id": f"a{i}", "source": "demo", "url": str(i), "title": "t", "content_text": "c", "summary": "s", "prompt_version": "v"}
        for i in range(5)
    ]
    export_splits(rows, tmp_path)
    assert (tmp_path / "train.jsonl").exists()
    assert (tmp_path / "val.jsonl").exists()
    assert (tmp_path / "test.jsonl").exists()
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
   - Split dataset: input fake -> output train/val/test.
2. Tạo file ghi chú `docs/run_checklist.md` hoặc ghi vào notebook cá nhân:
   - Cách tạo env.
   - Cách crawl thử 10 bài.
   - Cách label fake/Vertex.
   - Cách split dataset.
   - Cách chạy notebook.
   - Cách chạy web.
   - Cách chạy Docker.
3. Chạy các command thật:

```bash
python -m app.crawler --mode labeling --source vnexpress --limit 10 --output data/raw/articles.jsonl --verbose
python -m labeling.split_dataset --input data/labeled/labeled_articles.jsonl --output data/datasets/v2
uvicorn app.main:app --reload
python -m pytest tests_simple
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
| Tuần 1 | 0-1 | Code lại helper JSONL, schema, source config |
| Tuần 2 | 2-3 | Code RSS fetch, canonical URL, hash, rate limiter mini |
| Tuần 3 | 4-5 | Code extractor và mini crawler xuất JSONL |
| Tuần 4 | 6 | Code prompt/parser/fake labeling pipeline, hiểu cách thay bằng Vertex |
| Tuần 5 | 7 | Code QC và split train/val/test |
| Tuần 6 | 8 | Chạy notebook mini fine-tune flow, hiểu ViT5 + LoRA + ROUGE |
| Tuần 7 | 9 | Code inference class, hiểu lazy loading và batch summarize |
| Tuần 8 | 10-11 | Code FastAPI web demo, Docker, tests, checklist chạy dự án |

Nếu mỗi ngày chỉ có 1-2 giờ, có thể chia mỗi chặng thành 3 buổi:

1. Buổi 1: đọc lý thuyết và làm bài nhỏ.
2. Buổi 2: làm bài cuối chặng.
3. Buổi 3: so sánh với code dự án và viết ghi chú phỏng vấn.

## Thứ Tự Code Lại Dự Án Thật

Sau khi làm xong bài tập practice, bạn có thể tự code lại repo theo thứ tự này:

1. `app/schemas.py`
2. `app/sources.py`
3. Các helper JSONL trong `labeling/label_dataset.py`, `labeling/split_dataset.py`
4. `app/crawler.py` phần URL tools: `canonicalize_url`, `url_hash`
5. `app/crawler.py` phần RSS: `fetch_feed`, `_to_utc`, `_category_from_url`
6. `app/crawler.py` phần extract: `normalize_text`, `word_count`, `extract_from_html`
7. `app/crawler.py` phần pipeline: `crawl_articles`, `write_jsonl`, CLI
8. `labeling/prompt.py`
9. `labeling/vertex_labeler.py`
10. `labeling/label_dataset.py`
11. `labeling/qc.py`
12. `labeling/split_dataset.py`
13. `notebooks/finetune_vit5_lora.ipynb`
14. `app/summarizer.py`
15. `app/main.py`
16. `app/templates/index.html`
17. `Dockerfile`, `docker-compose.yml`
18. `tests_simple/`

## Acceptance Criteria Cuối Lộ Trình

Bạn hoàn thành lộ trình khi tự làm được các việc sau mà không cần copy code:

- Tự code crawler tạo được `data/raw/articles.jsonl`.
- Tự giải thích được vì sao crawler dùng RSS-first, canonical URL, robots/rate limit, dedupe.
- Tự code fake labeling pipeline và hiểu cách thay fake LLM bằng Vertex Gemini.
- Tự giải thích được prompt version `1.2.0` và vì sao report labeling là artifact lịch sử.
- Tự code QC và split dataset ra `train.jsonl`, `val.jsonl`, `test.jsonl`.
- Tự chạy và giải thích notebook fine-tune ViT5 + LoRA.
- Tự load model bằng `ViT5Summarizer` hoặc class tương tự và summarize text mới.
- Tự chạy web demo tại `http://localhost:8000`.
- Tự chạy Docker bằng `docker compose up --build`.
- Tự trả lời trong phỏng vấn:
  - Vì sao dùng Vertex để gán nhãn?
  - Vì sao dùng ViT5 cho tiếng Việt?
  - Vì sao dùng LoRA thay vì full fine-tune?
  - Vì sao dùng JSONL thay database?
  - Vì sao live crawl hôm nay không thể tạo lại y hệt dataset/report lịch sử?

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

Label dataset:

```bash
python -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl
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
python -m pytest tests_simple
```
