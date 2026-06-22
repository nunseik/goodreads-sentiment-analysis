# Goodreads Sentiment Analysis

Paste a Goodreads book URL and get an AI-generated sentiment summary from real reader reviews — with positive, neutral, and negative perspectives. Runs entirely in the browser; no server required.

Built as a learning project for Claude Code agent teams.

---

## How it works

1. Paste a Goodreads book URL (`goodreads.com/book/show/…`)
2. A Cloudflare Worker proxy fetches the page (bypasses CORS)
3. Reviews are parsed from the HTML (up to 30)
4. A WebLLM model running locally in your browser:
   - Picks the most positive, neutral, and negative review
   - Writes a balanced summary from all three perspectives
5. Results and per-model stats are cached in `localStorage`

Re-submit the same URL with a **different model** to add a second analysis alongside the first for comparison.

---

## Frontend (primary app)

A single HTML file — no build step, no dependencies to install.

**Open `frontend/index.html` in Chrome or Edge (113+).**

> WebGPU is required. Safari and Firefox are not supported.

### Models available

| Model | Size | Notes |
|---|---|---|
| Qwen 2.5 · 0.5B | ~390 MB | Fastest |
| Qwen 2.5 · 1.5B | ~970 MB | Default |
| Qwen 2.5 · 3B | ~1.9 GB | Better quality |
| Llama 3.2 · 1B | ~740 MB | Different style |

Models download once and are cached by the browser.

### Features

- **Model selector** — switch models per analysis; system requirements shown before first download
- **Multi-model comparison** — same book URL, different models → analyses stack in the result card
- **Inline stats** — time, token count, and tk/s stored per analysis and shown on every load
- **History panel** — side drawer listing all cached books; click to reload, delete per entry or clear all
- **30-day localStorage cache** — instant results for already-analyzed books

### LLM pipeline

Three sequential inference calls, then a summary:

1. **Pick positive** — identify the most enthusiastic review from the list
2. **Pick negative** — identify the most critical review
3. **Pick neutral** — identify the most balanced review
4. **Write summary** — generate a 4–5 sentence summary from all three perspectives

---

## Backend (optional, standalone)

A FastAPI server that does the same job server-side: Playwright scraping → VADER sentiment → Ollama summary. Independent of the frontend.

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) running locally with `gemma4:e2b-mlx`: `ollama pull gemma4:e2b-mlx`

### Running

```bash
cd backend
uv venv
uv pip install -r requirements.txt
uv run playwright install chromium
uv run uvicorn main:app --reload --port 8000
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze` | `{"book_title": "string"}` → summary, rating, author, Goodreads URL |
| `GET` | `/cache-stats` | SQLite cache stats |

### Backend pipeline

1. Scrapes Goodreads with Playwright (headless Chromium); falls back to mock data if blocked
2. VADER scores each review (compound score logged to console)
3. Selects a spread of reviews and calls Ollama for a summary
4. Persists results in `books.db` (SQLite, created automatically)

---

## Architecture

```
frontend/
└── index.html           # Single-file browser app (WebLLM + Cloudflare Worker proxy)

backend/
├── main.py              # FastAPI app + endpoints
├── scraper.py           # Playwright scraper (mock fallback on block)
├── vader_sentiment.py   # VADER sentiment scoring
├── ollama_summarizer.py # Review spread selection + Ollama summary
├── categorizer.py       # Review categorization helpers
├── database.py          # SQLite persistence
└── models.py            # Pydantic request/response types
```

---

## How this was built

Built with a **Claude Code agent team** — parallel agents working simultaneously:

- **Backend-Core agent** — `main.py`, `database.py`, `models.py`, `requirements.txt`
- **Pipeline agent** — `scraper.py`, `vader_sentiment.py`, `ollama_summarizer.py`
- **Frontend agent** — initial `frontend/index.html`

Subsequent iterations (WebLLM rewrite, history panel, multi-model support, stats) were added in follow-up Claude Code sessions.
