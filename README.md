# vn-news-summarizer

Vietnamese news summarization project simplified for an AI Engineer
intern portfolio.

The current version keeps the real project story and historical results:
RSS crawl -> Vertex AI Gemini teacher labels -> ViT5-base + LoRA
fine-tuning -> FastAPI web demo. It removes the production-heavy runtime
pieces from the main path: database, Alembic, Redis, scheduler, MLflow,
CI/CD, and Next.js.

## Ground Truth Results

The exact historical reports are preserved in:

- `docs/labeling_report.md`
- `docs/training_report.md`
- `docs/learning_roadmap.md`

Key numbers:

- Prompt `1.2.0`, Vertex `gemini-2.5-pro`, concurrency 5.
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
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ main.py                  # FastAPI app + web demo
â”‚   â”œâ”€â”€ crawler.py               # RSS crawl, extraction, robots, dedupe
â”‚   â”œâ”€â”€ summarizer.py            # ViT5/LoRA inference from HF or local path
â”‚   â”œâ”€â”€ sources.py               # Frozen RSS source config from RSS fix commit
â”‚   â””â”€â”€ templates/index.html
â”œâ”€â”€ labeling/
â”‚   â”œâ”€â”€ vertex_labeler.py        # Vertex Gemini wrapper
â”‚   â”œâ”€â”€ prompt.py                # Prompt v1.2.0 + robust JSON parser
â”‚   â”œâ”€â”€ qc.py                    # Deterministic QC checks
â”‚   â”œâ”€â”€ label_dataset.py         # raw articles JSONL -> labeled JSONL
â”‚   â””â”€â”€ split_dataset.py         # labeled JSONL -> train/val/test JSONL
â”œâ”€â”€ notebooks/finetune_vit5_lora.ipynb
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ raw/
â”‚   â”œâ”€â”€ labeled/
â”‚   â””â”€â”€ datasets/
â”œâ”€â”€ docs/
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ docker-compose.yml
â””â”€â”€ requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `HF_MODEL_ID` in `.env` to the model or LoRA adapter matching
`models/vit5-news-v2/checkpoint-309`.

## Run The Web Demo

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000`, then click **Tom tat tin tuc hom nay**.
The app crawls current RSS feeds, extracts article text, and summarizes
with the fine-tuned ViT5 model.

Docker:

```bash
docker compose up --build
```

## Build Dataset Artifacts

Crawl articles for labeling:

```bash
python -m app.crawler --mode labeling --output data/raw/articles.jsonl
```

Label with Vertex AI Gemini:

```bash
python -m labeling.label_dataset \
  --input data/raw/articles.jsonl \
  --output data/labeled/labeled_articles.jsonl \
  --concurrency 5
```

Export train/val/test splits:

```bash
python -m labeling.split_dataset \
  --input data/labeled/labeled_articles.jsonl \
  --output data/datasets/v2 \
  --check-v2-counts
```

`--check-v2-counts` should pass only when using the original v2 artifact.

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

## Tests

```bash
python -m pytest
```

The focused tests check the source configuration, prompt/parser
behavior, report numbers, and JSONL split schema.

