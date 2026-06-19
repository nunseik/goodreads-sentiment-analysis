import json
import re
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e2b-mlx"


def generate_summary(book_title: str, reviews: list[str], sentiment: dict) -> tuple[str, float]:
    """Returns (summary, rating). Rating is Ollama's estimate from 1.0–5.0."""
    sample = reviews[:5]
    sample_text = "\n".join(f"- {r[:200]}" for r in sample)
    mood = "positive" if sentiment["avg_compound"] > 0.1 else "mixed" if sentiment["avg_compound"] > -0.1 else "negative"

    prompt = (
        f"You are a literary critic. Based on the following reader reviews of \"{book_title}\", "
        f"produce a JSON object with exactly two keys:\n"
        f"  \"summary\": a concise 2-3 sentence paragraph of what readers think of the book\n"
        f"  \"rating\": your estimated star rating from 1.0 to 5.0 based on the reviews\n\n"
        f"The overall reader sentiment is {mood}.\n\n"
        f"Sample reviews:\n{sample_text}\n\n"
        f"Respond with only valid JSON, no markdown fences, no extra text."
    )

    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60,
        )
        resp.raise_for_status()
        raw = resp.json()["response"].strip()
        data = _parse_json(raw)
        summary = str(data.get("summary", "")).strip()
        rating = float(data.get("rating", sentiment["avg_star_rating"]))
        rating = max(1.0, min(5.0, rating))
        if not summary:
            raise ValueError("empty summary")
        return summary, round(rating, 1)
    except Exception:
        return _fallback_summary(book_title, sentiment), sentiment["avg_star_rating"]


def _parse_json(raw: str) -> dict:
    # Strip markdown fences if the model ignored instructions
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(cleaned)


def _fallback_summary(book_title: str, sentiment: dict) -> str:
    compound = sentiment["avg_compound"]
    if compound > 0.2:
        tone = "very positively"
    elif compound > 0:
        tone = "generally positively"
    elif compound > -0.2:
        tone = "with mixed feelings"
    else:
        tone = "negatively"
    avg_rating = sentiment["avg_star_rating"]
    return (
        f"Readers have responded {tone} to \"{book_title}\", giving it an average rating "
        f"of {avg_rating:.1f} out of 5. "
        f"The reviews reflect a {('mostly favourable' if compound > 0 else 'divided')} reception among readers."
    )
