# Goodreads Sentiment Analysis

A learning project demonstrating Claude Code agent teams. Two apps: a FastAPI backend and a single-file HTML frontend.

## What it does
1. User submits a book title in the frontend
2. Backend checks SQLite cache — returns immediately if found
3. On cache miss: scrapes Goodreads reviews using Playwright (headless Chromium)
   - Expands collapsed "...more" review text
   - Scrolls to load up to ~30 reviews
   - Falls back to mock data if Goodreads blocks the request
4. VADER sentiment analysis scores each review (logged to console for troubleshooting)
5. A spread of reviews (most positive, most negative, neutral) is selected and sent to Ollama
6. Ollama (gemma4:e2b-mlx) generates a 4-5 sentence human-readable summary + star rating estimate
7. Result stored in SQLite and returned to frontend

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) with gemma4:e2b-mlx: `ollama pull gemma4:e2b-mlx`

## Running the backend
```bash
cd backend
uv venv
uv pip install -r requirements.txt
uv run playwright install chromium
uv run uvicorn main:app --reload --port 8000
```

## Running the frontend
Open `frontend/index.html` directly in a browser. No build step needed.

## API endpoints
- `POST /analyze` — `{"book_title": "string"}` → returns summary, rating, author, Goodreads URL
- `GET /books` — lists all cached books

## Architecture
```
backend/
├── main.py              # FastAPI app + endpoints
├── scraper.py           # Playwright scraper (expands collapsed reviews, mock fallback on block)
├── vader_sentiment.py   # VADER sentiment scoring (logs compound score + stars to console)
├── ollama_summarizer.py # Selects review spread, calls Ollama gemma4:e2b-mlx for summary
├── database.py          # SQLite persistence (book_title, author, summary, avg_rating, goodreads_url)
└── models.py            # Pydantic request/response types
frontend/
└── index.html           # Single-file Vanilla JS UI (stars, author, Goodreads link)
```

## How this was built
This project was built using a **Claude Code agent team** — three parallel agents working simultaneously:
- **Backend-Core agent**: built `main.py`, `database.py`, `models.py`, `requirements.txt`
- **Pipeline agent**: built `scraper.py`, `vader_sentiment.py`, `ollama_summarizer.py`
- **Frontend agent**: built `frontend/index.html`

## Notes
- The scraper uses Playwright (headless Chromium) with browser-like headers. Goodreads may still block requests — the mock fallback ensures the pipeline always works.
- The SQLite database (`backend/books.db`) is created automatically on first run.
- Ollama must be running locally (`ollama serve`). If it's not, a template summary is generated from VADER data instead.
- VADER sentiment results are printed to the server console before each Ollama call — useful for troubleshooting.
