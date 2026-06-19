from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    book_title: str


class BookResponse(BaseModel):
    book_title: str
    author: str
    summary: str
    avg_rating: float
    goodreads_url: str
    cached: bool
