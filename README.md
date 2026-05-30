# vn-news-summarizer

Vietnamese news summarization project simplified for an AI Engineer
intern portfolio.

The current version keeps the real project story and historical results:
RSS crawl → Gemini teacher labels (AI Studio free keys) → ViT5-base + LoRA
fine-tuning → FastAPI web demo. It removes the production-heavy runtime
pieces from the main path: database, Alembic, Redis, scheduler, MLflow,
CI/CD, and Next.js.

## Ground Truth Results

The exact historical reports are preserved in `docs/learning_roadmap.md`.

Key numbers:

- Prompt `1.2.0`, `gemini-2.5-pro`, concurrency 5.
- 2412 labeled articles, 2070 QC-passed labels.
- Dataset v2: 1636 train / 218 val / 216 test.
- ViT5-base + LoRA test metrics: ROUGE-1 0.6055, ROUGE-2 0.3106,
  ROUGE-L 0.3804.

Live crawling today will not reproduce those counts because news feeds
change. The preserved dataset v2 and matching checkpoint/Hugging Face
model are required for exact metric reproduction.

## Simplified Structure

```text
vn-news-summarizer/
├── app/
│   ├── main.py                  # FastAPI app + web demo
│   ├── crawler.py               # RSS crawl, extraction, robots, dedupe
│   ├── summarizer.py            # ViT5/LoRA inference from HF or local path
│   ├── sources.py               # Frozen RSS source config from RSS fix commit
│   └── templates/index.html
├── labeling/
│   ├── gemini_labeler.py         # AI Studio Gemini (free keys + rotation)
│   ├── prompt.py                # Prompt v1.2.0 + robust JSON parser
│   ├── qc.py                    # Deterministic QC checks
│   ├── label_dataset.py         # raw articles JSONL → labeled JSONL
│   ├── io.py                    # Shared JSONL read/write helpers
│   └── split_dataset.py         # labeled JSONL → train/val/test JSONL
├── notebooks/finetune_vit5_lora.ipynb
├── data/
│   ├── raw/
│   ├── labeled/
│   └── datasets/
│       └── v2/                  # Committed training data: train/val/test.jsonl
├── models/                      # Put your fine-tuned checkpoint here (local inference)
├── docs/
├── streamlit_app.py             # Streamlit inference UI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Prerequisites

- **Python 3.11** (required — project uses `3.11` features, see `pyproject.toml`)
- **pip** (bundled with Python)
- **Git** (to clone this repo)
- **(Optional)** Docker & Docker Compose — for containerized deployment

## Setup (Local)

### 1. Clone the repository

```bash
git clone https://github.com/king14052004-crypto/vn-news-summarizer.git
cd vn-news-summarizer
```

### 2. Create and activate a virtual environment

**Linux / macOS:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

Then edit `.env` and set the required values:

```dotenv
# Run locally with your fine-tuned checkpoint (no Hugging Face needed):
HF_MODEL_ID=models/vit5-news-v2
HF_BASE_MODEL_ID=VietAI/vit5-base
HF_TOKEN=              # optional — only for private Hugging Face repos

# For Gemini labeling (see "Build Dataset Artifacts" below)
GEMINI_API_KEYS=key1,key2,key3,key4,key5
```

## Use a Local Fine-tuned Model (no Hugging Face)

`HF_MODEL_ID` accepts **either** a Hugging Face repo id **or a local path**, so
you can run entirely offline with the checkpoint produced by the notebook.

1. The training notebook saves to `OUTPUT_DIR = models/vit5-news-v2` via
   `trainer.save_model(...)` + `tokenizer.save_pretrained(...)`, and also writes
   per-epoch checkpoints (`models/vit5-news-v2/checkpoint-XXX`). Because LoRA is
   used, this folder is a small **adapter**, not a full model.
2. Copy that folder into this repo under `models/` (the folder is git-ignored, so
   large weights never get committed):

   ```text
   models/
   └── vit5-news-v2/
       ├── adapter_config.json
       ├── adapter_model.safetensors
       ├── tokenizer.json / spiece.model / ...
       └── checkpoint-309/        # (optional) a specific epoch
   ```
3. Point `.env` at the local folder and set the base model the adapter sits on:

   ```dotenv
   HF_MODEL_ID=models/vit5-news-v2          # or models/vit5-news-v2/checkpoint-309
   HF_BASE_MODEL_ID=VietAI/vit5-base
   ```

`app/summarizer.py` auto-detects a LoRA adapter and loads `HF_BASE_MODEL_ID` as
the base; if the adapter folder has no tokenizer it falls back to the base
model's tokenizer. The only thing fetched from the internet in this case is the
public `VietAI/vit5-base` base model (cached after the first run).

## Run the Web Demo

### Option 1 — Streamlit UI (recommended)

```bash
streamlit run streamlit_app.py
```

Open <http://localhost:8501>. The Streamlit UI provides:
- **Nhập văn bản**: Paste article text manually and get a summary.
- **Crawl tin mới**: Crawl today's RSS feeds and summarize automatically.

### Option 2 — FastAPI (API-first)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000>, then click **Tóm tắt tin tức hôm nay**.

### Docker

```bash
docker compose up --build
```

The FastAPI is exposed at <http://localhost:8000>.

## Build Dataset Artifacts

> **Already included:** the curated training data ships with the repo at
> `data/datasets/v2/` (`train.jsonl` 1636 / `val.jsonl` 218 / `test.jsonl` 216),
> so you can go straight to **Fine-tuning** without re-running the pipeline below.
> Follow these steps only when you want to build a fresh dataset from new crawls.

The labeling pipeline uses **gemini-3.1-flash-lite** via free AI Studio
API keys. Keys are rotated **round-robin** — every call starts on a different
key, so all keys you provide share the load (not just the first few), and a key
is only skipped for a request when it returns a rate-limit/transient error.

### Step 1 — Crawl articles for labeling

```bash
python -m app.crawler --mode labeling --output data/raw/articles.jsonl
```

### Step 2 — Label with Gemini

Get one or more free API keys at <https://aistudio.google.com/apikey>,
then set them in your `.env` or export directly:

```bash
export GEMINI_API_KEYS=key1,key2,key3
```

```bash
python -m labeling.label_dataset \
  --input data/raw/articles.jsonl \
  --output data/labeled/labeled_articles.jsonl \
  --concurrency 5
```

### Step 3 — Export train/val/test splits

```bash
python -m labeling.split_dataset \
  --input data/labeled/labeled_articles.jsonl \
  --output data/datasets/v2 \
  --check-v2-counts
```

`--check-v2-counts` passes only when using the original v2 artifact.

## Fine-tuning

Use `notebooks/finetune_vit5_lora.ipynb`. The notebook keeps the v2
training values directly in the notebook for readability:

- `VietAI/vit5-base`
- max input/target length `1024/128`
- 4 epochs
- train batch size 4, gradient accumulation 4
- learning rate `5e-5`
- fp16
- LoRA `r=16`, `alpha=32`, `dropout=0.05`, target modules `q`, `v`
- seed `42`

## Makefile Shortcuts

| Command              | Description                                      |
|----------------------|--------------------------------------------------|
| `make setup`         | Install dependencies from `requirements.txt`     |
| `make crawl-labeling`| Crawl articles into `data/raw/articles.jsonl`    |
| `make label`         | Label articles with Gemini (concurrent mode)     |
| `make split`         | Export QC-passed labels to `data/datasets/v2`    |
| `make api`           | Run FastAPI demo on `http://localhost:8000`       |
| `make streamlit`     | Run Streamlit UI on `http://localhost:8501`       |
| `make docker-up`     | Build and run the demo container                 |
| `make docker-down`   | Stop the demo container                          |

## Environment Variables Reference

| Variable               | Required | Default           | Description                                       |
|------------------------|----------|-------------------|---------------------------------------------------|
| `HF_MODEL_ID`         | Yes      | `VietAI/vit5-base`| HF repo id **or local path** (e.g. `models/vit5-news-v2`) |
| `HF_BASE_MODEL_ID`    | No       | *(from adapter)*  | Override base model for PEFT/LoRA adapters        |
| `HF_TOKEN`            | No       | —                 | Hugging Face token (for private models)           |
| `MODEL_DEVICE`        | No       | *(auto)*          | Device for inference (`cpu`, `cuda`, `mps`)       |
| `MAX_ARTICLES_PER_DEMO`| No      | `5`               | Max articles crawled per demo request             |
| `GEMINI_API_KEYS`     | For labeling | —             | Comma-separated AI Studio API keys                |
| `GEMINI_API_KEY`      | For labeling | —             | Single AI Studio API key (alternative)            |
| `API_HOST`            | No       | `0.0.0.0`         | FastAPI bind host                                 |
| `API_PORT`            | No       | `8000`            | FastAPI bind port                                 |

## License

MIT
