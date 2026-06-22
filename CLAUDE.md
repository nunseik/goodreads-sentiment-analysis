# Goodreads Sentiment Analysis

A learning project demonstrating Claude Code agent teams. The **primary app** is a browser-only single-file frontend. The backend is a standalone alternative that does the same job server-side.

## What it does

1. User pastes a Goodreads book URL in the frontend
2. A Cloudflare Worker proxy fetches the page (bypasses CORS)
3. Reviews are parsed from the HTML (up to 30)
4. A WebLLM model running in the browser runs a 3-step pipeline:
   - Pick most positive review
   - Pick most neutral review
   - Pick most negative review
   - Write a balanced summary from all three
5. Results cached in `localStorage` with a 30-day TTL per model+URL combo

## Architecture

```
frontend/
└── index.html           # Single-file browser app — no build step

backend/
├── main.py              # FastAPI app + endpoints
├── scraper.py           # Playwright scraper (mock fallback on Goodreads block)
├── vader_sentiment.py   # VADER sentiment scoring
├── ollama_summarizer.py # Ollama (gemma4:e2b-mlx) summary generation
├── categorizer.py       # Review categorization helpers
├── database.py          # SQLite persistence (books.db, auto-created)
└── models.py            # Pydantic request/response types
```

## Running the frontend

Open `frontend/index.html` directly in Chrome 113+ or Edge 113+. No build step needed.

- WebGPU required — Safari and Firefox not supported
- Models download once and are cached by the browser
- Cloudflare Worker proxy: `https://fetch-page.nunseik.workers.dev/`

## Running the backend

```bash
cd backend
uv venv
uv pip install -r requirements.txt
uv run playwright install chromium
uv run uvicorn main:app --reload --port 8000
```

Requires Ollama running locally: `ollama pull gemma4:e2b-mlx`

## Frontend features

- **Model selector** — 4 WebLLM models (Qwen 2.5: 0.5B/1.5B/3B, Llama 3.2 1B); engine reloads on model change
- **System requirements modal** — shown before first download of each model; acknowledgment stored per model ID in localStorage (`req-ack:<modelId>`)
- **Multi-model analysis** — cache stores an `analyses` array per URL; submitting same URL with different model appends rather than overwrites
- **Inline stats** — each analysis stores `{ totalMs, totalTokens }` and displays time / tokens / tk/s
- **History drawer** — lists all cached books from localStorage; click to reload, per-item delete, clear all

## Cache format (localStorage)

Key: `bsa:<goodreads-url>`

```json
{
  "ts": 1234567890000,
  "data": {
    "title": "...",
    "author": "...",
    "avg_rating": 3.9,
    "goodreads_url": "...",
    "analyses": [
      {
        "modelId": "Qwen2.5-1.5B-Instruct-q4f16_1-MLC",
        "modelName": "Qwen 2.5 · 1.5B",
        "ts": 1234567890000,
        "summary": "...",
        "positive": "...",
        "negative": "...",
        "stats": { "totalMs": 14200, "totalTokens": 312 }
      }
    ]
  }
}
```

Old cache entries (pre-multi-model) with a flat `summary/positive/negative` structure are migrated automatically by `migrateData()` on read.

## Backend API

- `POST /analyze` — `{"book_title": "string"}` → summary, rating, author, Goodreads URL
- `GET /cache-stats` — SQLite cache info

## How this was built

Built with a **Claude Code agent team** — three parallel agents for the initial version, then iterative Claude Code sessions for subsequent features.
