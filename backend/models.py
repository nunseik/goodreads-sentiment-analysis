from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    book_title: str


class BookResponse(BaseModel):
    book_title: str
    summary: str
    avg_rating: float
    cached: bool
