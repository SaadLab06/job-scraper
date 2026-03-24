"""
Bayt.com scraper — largest job board for the MENA region.
Scrapes the public job listing pages (no auth required for basic listings).

Coverage: UAE, Saudi Arabia, Egypt, Kuwait, Qatar, Jordan, Lebanon, etc.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# Search queries targeting MENA tech market
SEARCH_QUERIES = [
    ("software engineer", ""),
    ("python developer", ""),
    ("full stack developer", ""),
    ("data scientist", ""),
    ("frontend developer", "Dubai"),
    ("backend developer", "Riyadh"),
    ("mobile developer", ""),
    ("devops engineer", ""),
]

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _parse_date(text: str) -> Optional[datetime]:
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    if "today" in text or "just" in text:
        return now
    m = re.search(r"(\d+)\s*(day|week|month)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == "day":
            return now - timedelta(days=n)
        if unit == "week":
            return now - timedelta(weeks=n)
        if unit == "month":
            return now - timedelta(days=n * 30)
    return None


class BaytScraper(BaseScraper):
    source = "bayt"

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        for keyword, location in SEARCH_QUERIES:
            try:
                batch = await self._fetch_query(keyword, location)
                jobs.extend(batch)
                logger.info("Bayt: %d jobs for '%s'", len(batch), keyword)
            except Exception as exc:
                logger.warning("Bayt query '%s' failed: %s", keyword, exc)
        return jobs

    async def _fetch_query(self, keyword: str, location: str) -> list[RawJob]:
        from urllib.parse import urlencode, quote_plus

        # Bayt search URL pattern
        kw_slug = quote_plus(keyword.replace(" ", "-"))
        base = f"https://www.bayt.com/en/international/jobs/{kw_slug}-jobs/"
        params: dict = {}
        if location:
            params["l"] = location

        url = f"{base}?{urlencode(params)}" if params else base
        resp = await self.get(url, headers={"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"})
        soup = BeautifulSoup(resp.text, "lxml")

        jobs: list[RawJob] = []

        # Bayt listing cards
        cards = soup.select("li[data-job-id], div.has-pointer-d")

        for card in cards:
            try:
                title_el = card.select_one("h2.m0.t-bold a, h2 a[data-js-aid='jobTitle']")
                company_el = card.select_one("b[itemprop='name'], span[data-js-aid='company-name']")
                location_el = card.select_one("span.t-mute.m0, [data-js-aid='job-location']")
                date_el = card.select_one("span.m0.t-mute.t-small, time")
                link_el = title_el  # title is the link

                title = title_el.get_text(strip=True) if title_el else None
                company = company_el.get_text(strip=True) if company_el else None
                loc = location_el.get_text(strip=True) if location_el else None

                if not title or not company:
                    continue

                href = link_el.get("href", "") if link_el else ""
                job_url = f"https://www.bayt.com{href}" if href.startswith("/") else href

                posted_at = None
                if date_el:
                    posted_at = _parse_date(date_el.get_text(strip=True))

                is_remote = bool(loc and "remote" in loc.lower())

                jobs.append(
                    RawJob(
                        title=title,
                        company=company,
                        location=loc,
                        url=job_url,
                        source=self.source,
                        is_remote=is_remote,
                        posted_at=posted_at,
                    )
                )
            except Exception:
                continue

        return jobs
