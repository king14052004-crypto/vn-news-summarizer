PY ?= python
PIP ?= pip

.PHONY: help setup crawl-labeling label split api streamlit docker-up docker-down

help:
	@echo "setup          Install dependencies from requirements.txt"
	@echo "crawl-labeling Crawl articles for labeling into data/raw/articles.jsonl"
	@echo "label          Label crawled articles with Gemini (AI Studio by default)"
	@echo "split          Export QC-passed labels to data/datasets/v2"
	@echo "api            Run FastAPI demo on http://localhost:8000"
	@echo "streamlit      Run Streamlit UI on http://localhost:8501"
	@echo "docker-up      Build and run the demo container"

setup:
	$(PIP) install -r requirements.txt

crawl-labeling:
	$(PY) -m app.crawler --mode labeling --output data/raw/articles.jsonl

label:
	$(PY) -m labeling.label_dataset --input data/raw/articles.jsonl --output data/labeled/labeled_articles.jsonl --concurrency 5

split:
	$(PY) -m labeling.split_dataset --input data/labeled/labeled_articles.jsonl --output data/datasets/v2

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

streamlit:
	streamlit run streamlit_app.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
