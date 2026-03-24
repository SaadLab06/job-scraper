"""
LinkedIn scraper — uses Playwright to fetch the public job search page.

IMPORTANT:
  - This scraper operates on public-facing, non-authenticated pages only.
  - LinkedIn's ToS restricts automated scraping. Use conservatively:
    long delays, low frequency, proxy rotation in production.
  - Schedule at most once per 12 hours per search query.
  - If you receive a C&D, disable this scraper in celery_app.py beat schedule.
"""

from __future__ import annotations

import asyncio
import logging
import re
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# Public LinkedIn job search URLs (no auth required)
SEARCH_QUERIES = [
    ("software engineer", "remote"),
    ("python developer", ""),
    ("backend engineer", "remote"),
    ("data scientist", ""),
    ("frontend engineer", "remote"),
]

_STEALTH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def _parse_relative_time(text: str) -> Optional[datetime]:
    """Parse LinkedIn relative post times like '2 days ago', '1 week ago'."""
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    patterns = [
        (r"(\d+)\s+minute", "minutes"),
        (r"(\d+)\s+hour", "hours"),
        (r"(\d+)\s+day", "days"),
        (r"(\d+)\s+week", "weeks"),
        (r"(\d+)\s+month", "months"),
    ]
    for pattern, unit in patterns:
        m = re.search(pattern, text)
        if m:
            n = int(m.group(1))
            if unit == "minutes":
                return now - timedelta(minutes=n)
            if unit == "hours":
                return now - timedelta(hours=n)
            if unit == "days":
                return now - timedelta(days=n)
            if unit == "weeks":
                return now - timedelta(weeks=n)
            if unit == "months":
                return now - timedelta(days=n * 30)
    return None


class LinkedInScraper(BaseScraper):
    source = "linkedin"

    async def fetch_jobs(self) -> list[RawJob]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: playwright install chromium")
            return []

        jobs: list[RawJob] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                user_agent=_STEALTH_UA,
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )

            # Disable webdriver detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            """)

            for keyword, location in SEARCH_QUERIES:
                try:
                    page_jobs = await self._scrape_search(context, keyword, location)
                    jobs.extend(page_jobs)
                    logger.info(
                        "LinkedIn: %d jobs for '%s %s'", len(page_jobs), keyword, location
                    )
                except Exception as exc:
                    logger.warning("LinkedIn search failed for '%s': %s", keyword, exc)
                finally:
                    # Respectful delay between queries (5-10s random)
                    await asyncio.sleep(random.uniform(5, 10))

            await browser.close()

        return jobs

    async def _scrape_search(self, context, keyword: str, location: str) -> list[RawJob]:
        from urllib.parse import urlencode

        params = {"keywords": keyword, "f_TP": "1,2,3,4"}  # f_TP = date filter
        if location:
            params["location"] = location
        url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"

        page = await context.new_page()
        jobs: list[RawJob] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(random.uniform(2, 4))  # wait for lazy load

            # Scroll to load more listings
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)

            cards = await page.query_selector_all("div.job-search-card, li.jobs-search-results__list-item")

            for card in cards[:25]:  # cap per query
                try:
                    title_el = await card.query_selector(
                        "h3.base-search-card__title, .job-card-list__title"
                    )
                    company_el = await card.query_selector(
                        "h4.base-search-card__subtitle, .job-card-container__company-name"
                    )
                    location_el = await card.query_selector(
                        "span.job-search-card__location, .job-card-container__metadata-item"
                    )
                    link_el = await card.query_selector(
                        "a.base-card__full-link, a.job-card-list__title"
                    )
                    time_el = await card.query_selector("time")

                    title = (await title_el.inner_text()).strip() if title_el else None
                    company = (await company_el.inner_text()).strip() if company_el else None
                    location = (await location_el.inner_text()).strip() if location_el else None
                    url_val = await link_el.get_attribute("href") if link_el else None
                    time_text = await time_el.get_attribute("datetime") if time_el else None

                    if not title or not company or not url_val:
                        continue

                    # Clean LinkedIn tracking params from URL
                    clean_url = url_val.split("?")[0] if url_val else url_val

                    is_remote = bool(location and "remote" in location.lower())

                    posted_at: Optional[datetime] = None
                    if time_text:
                        try:
                            posted_at = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
                        except ValueError:
                            posted_at = _parse_relative_time(time_text)

                    jobs.append(
                        RawJob(
                            title=title,
                            company=company,
                            location=location,
                            url=clean_url,
                            source=self.source,
                            is_remote=is_remote,
                            posted_at=posted_at,
                        )
                    )
                except Exception:
                    continue
        finally:
            await page.close()

        return jobs
