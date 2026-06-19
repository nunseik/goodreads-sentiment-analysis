# Goodreads Sentiment Analysis

A learning project demonstrating Claude Code agent teams. Two apps: a FastAPI backend and a single-file HTML frontend.

## What it does
1. User submits a book title in the frontend
2. Backend checks SQLite cache — returns immediately if found
3. On cache miss: scrapes Goodreads reviews (falls back to mock data if blocked)
4. VADER sentiment analysis scores each review
5. Ollama (gemma4:e2b-mlx) generates a human-readable summary
6. Result stored in SQLite and returned to frontend

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) with gemma4:e2b-mlx: `ollama pull gemma4:e2b-mlx`

## Running the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Running the frontend
Open `frontend/index.html` directly in a browser. No build step needed.

## API endpoints
- `POST /analyze` — `{"book_title": "string"}` → returns summary + rating
- `GET /books` — lists all cached books

## Architecture
```
backend/
├── main.py              # FastAPI app + endpoints
├── scraper.py           # Goodreads HTML scraper (mock fallback on 403)
├── vader_sentiment.py   # VADER sentiment scoring
├── ollama_summarizer.py # Ollama gemma4:e2b-mlx summary generation
├── database.py          # SQLite persistence
└── models.py            # Pydantic request/response types
frontend/
└── index.html           # Single-file Vanilla JS UI
```

## How this was built
This project was built using a **Claude Code agent team** — three parallel agents working simultaneously:
- **Backend-Core agent**: built `main.py`, `database.py`, `models.py`, `requirements.txt`
- **Pipeline agent**: built `scraper.py`, `vader_sentiment.py`, `ollama_summarizer.py`
- **Frontend agent**: built `frontend/index.html`

## Notes
- The scraper uses browser-like headers but Goodreads may still block requests. The mock fallback ensures the pipeline always works.
- The SQLite database (`backend/books.db`) is created automatically on first run.
- Ollama must be running locally. If it's not, a template summary is generated from VADER data instead.
