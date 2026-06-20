CATEGORY_KEYWORDS = {
    "plot": [
        "plot", "story", "storyline", "narrative", "ending", "twist",
        "beginning", "middle", "conclusion", "arc", "subplot",
    ],
    "characters": [
        "character", "protagonist", "hero", "heroine", "villain", "cast",
        "relationship", "dialogue", "voice",
    ],
    "writing": [
        "writing", "prose", "style", "language", "sentence", "word",
        "author's", "descriptive", "lyrical", "poetic",
    ],
    "pacing": [
        "pacing", "pace", "slow", "fast", "dragged", "rushed",
        "couldn't put", "page-turner", "boring", "gripping",
    ],
}


def categorize_reviews(reviews: list[str]) -> dict[str, list[str]]:
    """Groups reviews by theme. Returns dict with keys: plot, characters, writing, pacing, other."""
    categories: dict[str, list[str]] = {
        "plot": [],
        "characters": [],
        "writing": [],
        "pacing": [],
        "other": [],
    }

    for review in reviews:
        lowered = review.lower()
        matched = False
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                categories[category].append(review)
                matched = True
        if not matched:
            categories["other"].append(review)

    return categories


def get_category_summary(categories: dict[str, list[str]]) -> dict[str, int]:
    """Returns count of reviews per category."""
    return {category: len(reviews) for category, reviews in categories.items()}
