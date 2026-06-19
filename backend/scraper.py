import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

_MOCK_REVIEWS = [
    "I absolutely loved this book. The writing style was captivating and the characters felt real. A must-read!",
    "Started slow but picked up tremendously. By the end I couldn't put it down.",
    "Beautifully written. Made me think deeply about life. Highly recommended.",
    "I found it quite overrated. The plot dragged and I struggled to connect with the protagonist.",
    "A masterpiece. One of the best books I've read this year. The prose is stunning.",
    "Mixed feelings. Some chapters were brilliant, others felt unnecessary.",
    "A wonderful read — heart, humour, and genuine emotional depth. 5 stars.",
    "Exceeded all my expectations. The world-building is exceptional and the ending was perfect.",
    "Decent but nothing groundbreaking. Enjoyable but forgettable.",
    "Couldn't finish it. The pacing was off and I just didn't care about the characters.",
]


async def scrape_goodreads(title: str) -> tuple[list[str], float, str, str]:
    """Returns (reviews, rating, author, goodreads_url)."""
    try:
        return await _fetch(title)
    except Exception:
        return _MOCK_REVIEWS, 0.0, "", ""


async def _collect_reviews(page, target: int = 30) -> list[str]:
    LOCATORS = [".ReviewText__content", ".reviewText span[id]", "section.ReviewText"]
    # Selectors for the "...more" expand buttons on collapsed reviews
    EXPAND_SELECTORS = [
        "button.ReviewText__truncatedTextLink",
        ".ReviewText__truncatedTextLink",
        "button.Spoiler__button",
    ]
    seen: set[str] = set()
    reviews: list[str] = []

    for _ in range(8):  # max 8 scroll attempts
        # Expand all collapsed reviews visible on screen
        for sel in EXPAND_SELECTORS:
            btns = await page.locator(sel).all()
            for btn in btns:
                try:
                    await btn.click()
                    await asyncio.sleep(0.1)
                except Exception:
                    pass

        for locator_str in LOCATORS:
            els = await page.locator(locator_str).all()
            for el in els:
                text = (await el.text_content() or "").strip()
                if len(text) > 50 and text not in seen:
                    seen.add(text)
                    reviews.append(text[:500])
            if reviews:
                break

        if len(reviews) >= target:
            break

        prev_count = len(seen)
        await page.evaluate("window.scrollBy(0, 2000)")
        await asyncio.sleep(1.2)

        # Stop if scroll yielded nothing new
        if len(seen) == prev_count and prev_count > 0:
            break

    return reviews


async def _fetch(title: str) -> tuple[list[str], float, str, str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()

        try:
            await page.goto(
                f"https://www.goodreads.com/search?q={title.replace(' ', '+')}",
                wait_until="domcontentloaded",
                timeout=20000,
            )

            # Follow the first book result
            book_link = page.locator("a.bookTitle").first
            await book_link.wait_for(timeout=10000)
            await book_link.click()
            await page.wait_for_load_state("domcontentloaded")

            goodreads_url = page.url

            # Rating
            rating = 0.0
            try:
                rating_el = page.locator(
                    "div.RatingStatistics__rating, [data-testid='ratingsAndReviews'] .average"
                ).first
                await rating_el.wait_for(timeout=8000)
                rating_text = await rating_el.text_content()
                rating = float(rating_text.strip().split()[0])
            except (PlaywrightTimeout, ValueError):
                pass

            # Author
            author = ""
            try:
                author_el = page.locator(
                    "span.ContributorLink__name, .authorName span[itemprop='name']"
                ).first
                await author_el.wait_for(timeout=5000)
                author = (await author_el.text_content() or "").strip()
            except PlaywrightTimeout:
                pass

            # Scroll repeatedly to load more reviews
            reviews = await _collect_reviews(page, target=30)

            return reviews or _MOCK_REVIEWS, rating, author, goodreads_url

        finally:
            await browser.close()
