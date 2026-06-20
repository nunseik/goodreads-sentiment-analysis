import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "books.db"

CACHE_TTL_DAYS = 30


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                book_title TEXT UNIQUE NOT NULL,
                author TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL,
                avg_rating REAL NOT NULL,
                goodreads_url TEXT NOT NULL DEFAULT '',
                reviews_raw TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        try:
            conn.execute("ALTER TABLE books ADD COLUMN updated_at TIMESTAMP")
            conn.execute("UPDATE books SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists


def get_book(title: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            f"""SELECT book_title, author, summary, avg_rating, goodreads_url
                FROM books
                WHERE LOWER(book_title) = LOWER(?)
                  AND updated_at > datetime('now', '-{CACHE_TTL_DAYS} days')""",
            (title,)
        ).fetchone()
    return dict(row) if row else None


def save_book(title: str, author: str, summary: str, avg_rating: float, goodreads_url: str, reviews: list[str]):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO books (book_title, author, summary, avg_rating, goodreads_url, reviews_raw, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (title, author, summary, avg_rating, goodreads_url, json.dumps(reviews))
        )
        conn.commit()


def get_cache_stats() -> dict:
    """Returns total books cached, fresh count, stale count."""
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        fresh = conn.execute(
            f"SELECT COUNT(*) FROM books WHERE updated_at > datetime('now', '-{CACHE_TTL_DAYS} days')"
        ).fetchone()[0]
    return {
        "total": total,
        "fresh": fresh,
        "stale": total - fresh,
        "ttl_days": CACHE_TTL_DAYS,
    }
