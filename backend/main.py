from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from database import get_book, init_db, save_book
from models import AnalyzeRequest, BookResponse
from scraper import scrape_goodreads
from vader_sentiment import analyze_reviews
from ollama_summarizer import generate_summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Goodreads Sentiment Analysis", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=BookResponse)
async def analyze_book(request: AnalyzeRequest):
    title = request.book_title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="book_title must not be empty")

    cached = get_book(title)
    if cached:
        return BookResponse(**cached, cached=True)

    reviews, scraped_rating, author, goodreads_url = await scrape_goodreads(title)
    sentiment = analyze_reviews(reviews)
    summary, llm_rating = generate_summary(title, reviews, sentiment)
    avg_rating = round(scraped_rating if scraped_rating > 0 else llm_rating, 2)

    save_book(title, author, summary, avg_rating, goodreads_url, reviews)
    return BookResponse(
        book_title=title, author=author, summary=summary,
        avg_rating=avg_rating, goodreads_url=goodreads_url, cached=False,
    )


@app.get("/books")
async def list_books():
    import sqlite3
    from database import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT book_title, avg_rating, created_at FROM books ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]
