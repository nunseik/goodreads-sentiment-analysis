import json
import re
import httpx

from categorizer import categorize_reviews, get_category_summary

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e2b-mlx"


def generate_summary(book_title: str, reviews: list[str], sentiment: dict) -> tuple[str, float]:
    """Returns (summary, rating). Rating is Ollama's estimate from 1.0–5.0."""
    sample = _select_reviews(reviews, sentiment["breakdown"])
    sample_text = "\n".join(f'- "{r[:250]}"' for r in sample)
    mood = "positive" if sentiment["avg_compound"] > 0.1 else "mixed" if sentiment["avg_compound"] > -0.1 else "negative"

    categories = categorize_reviews(reviews)
    cat_summary = get_category_summary(categories)
    themes_line = ", ".join(f"{k}: {v} reviews" for k, v in cat_summary.items() if v > 0)

    prompt = (
        f"You are a literary critic writing for a book review website. "
        f"Based on the reader reviews of \"{book_title}\" below, produce a JSON object with exactly two keys:\n"
        f"  \"summary\": 4-5 sentences covering what readers specifically praised or criticised. "
        f"Open with an overall impression, then go deeper — mention writing style, characters, plot, or pacing "
        f"as the reviews highlight them, including any notable criticisms or divisive opinions. "
        f"Vary your sentence structure. Do not open with 'Readers' or repeat the book title in every sentence. "
        f"Be specific and vivid, not generic.\n"
        f"  \"rating\": your estimated star rating from 1.0 to 5.0 based on the reviews\n\n"
        f"Review themes mentioned: {themes_line}\n"
        f"Overall sentiment: {mood} (avg rating {sentiment['avg_star_rating']:.1f}/5)\n\n"
        f"Reviews (mix of positive, negative, and neutral):\n{sample_text}\n\n"
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


def _select_reviews(reviews: list[str], breakdown: list[dict]) -> list[str]:
    """Pick a sentiment spread plus at least one review from each non-empty theme."""
    if len(reviews) <= 5:
        return reviews

    paired = sorted(
        zip(breakdown, reviews),
        key=lambda x: x[0]["compound"]
    )
    most_negative = [r for _, r in paired[:2]]
    most_positive = [r for _, r in paired[-2:]]

    mid = len(paired) // 2
    neutral = [paired[mid][1]]

    selected = most_positive + most_negative + neutral

    categories = categorize_reviews(reviews)
    for theme_reviews in categories.values():
        if theme_reviews and not any(r in selected for r in theme_reviews):
            selected.append(theme_reviews[0])

    return selected


def _parse_json(raw: str) -> dict:
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
