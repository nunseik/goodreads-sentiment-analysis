import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "books.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                book_title TEXT UNIQUE NOT NULL,
                summary TEXT NOT NULL,
                avg_rating REAL NOT NULL,
                reviews_raw TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_book(title: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT book_title, summary, avg_rating FROM books WHERE LOWER(book_title) = LOWER(?)",
            (title,)
        ).fetchone()
    return dict(row) if row else None


def save_book(title: str, summary: str, avg_rating: float, reviews: list[str]):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO books (book_title, summary, avg_rating, reviews_raw)
               VALUES (?, ?, ?, ?)""",
            (title, summary, avg_rating, json.dumps(reviews))
        )
        conn.commit()
