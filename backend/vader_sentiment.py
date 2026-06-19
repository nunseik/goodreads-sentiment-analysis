from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_reviews(reviews: list[str]) -> dict:
    if not reviews:
        return {"avg_compound": 0.0, "avg_star_rating": 3.0, "breakdown": []}

    scores = [_analyzer.polarity_scores(r) for r in reviews]
    avg_compound = sum(s["compound"] for s in scores) / len(scores)

    avg_star_rating = _compound_to_stars(avg_compound)

    breakdown = [
        {"review": r[:100] + "..." if len(r) > 100 else r, "compound": s["compound"]}
        for r, s in zip(reviews, scores)
    ]

    return {
        "avg_compound": round(avg_compound, 4),
        "avg_star_rating": round(avg_star_rating, 2),
        "breakdown": breakdown,
    }


def _compound_to_stars(compound: float) -> float:
    return 1.0 + (compound + 1.0) / 2.0 * 4.0
