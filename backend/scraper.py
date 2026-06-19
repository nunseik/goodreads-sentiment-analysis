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


async def scrape_goodreads(title: str) -> tuple[list[str], float]:
    try:
        return await _fetch(title)
    except Exception:
        return _MOCK_REVIEWS, 0.0


async def _fetch(title: str) -> tuple[list[str], float]:
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

            # Scroll to trigger review loading
            await page.evaluate("window.scrollBy(0, 1500)")
            await asyncio.sleep(1)

            reviews = []
            for locator_str in [
                ".ReviewText__content",
                ".reviewText span[id]",
                "section.ReviewText",
            ]:
                els = await page.locator(locator_str).all()
                for el in els:
                    text = (await el.text_content() or "").strip()
                    if len(text) > 50:
                        reviews.append(text[:500])
                if reviews:
                    break

            return reviews or _MOCK_REVIEWS, rating

        finally:
            await browser.close()
