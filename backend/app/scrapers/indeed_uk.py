"""
Indeed UK scraper — HTML scraping of uk.indeed.com public search results.
Mirrors the structure of the Indeed US scraper but uses the UK domain and
adjusts salary parsing for GBP.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    ("software engineer", ""),
    ("python developer", ""),
    ("backend developer", "London"),
    ("data scientist", ""),
    ("react developer", ""),
    ("devops engineer", ""),
    ("machine learning engineer", ""),
]

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def _parse_salary_gbp(text: str) -> tuple[Optional[float], Optional[float], str]:
    """
    Parse GBP salary strings like '£40,000 - £60,000 a year' or '£20 an hour'.
    Returns (min, max, currency).
    """
    text = text.replace(",", "")
    annual_match = re.search(r"£([\d.]+)\s*[-–]\s*£([\d.]+)\s*a?\s*year", text, re.I)
    if annual_match:
        return float(annual_match.group(1)), float(annual_match.group(2)), "GBP"

    single_match = re.search(r"£([\d.]+)\s*a?\s*year", text, re.I)
    if single_match:
        v = float(single_match.group(1))
        return v, v, "GBP"

    hourly = re.search(r"£([\d.]+)\s*an?\s*hour", text, re.I)
    if hourly:
        h = float(hourly.group(1))
        annual = h * 40 * 52
        return annual, annual, "GBP"

    return None, None, "GBP"


def _parse_posted_date(text: str) -> Optional[datetime]:
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    if "just posted" in text or "today" in text:
        return now
    m = re.search(r"(\d+)\s+day", text)
    if m:
        return now - timedelta(days=int(m.group(1)))
    return None


class IndeedUKScraper(BaseScraper):
    source = "indeed_uk"

    async def fetch_jobs(self) -> list[RawJob]:
        import random
        jobs: list[RawJob] = []

        for keyword, location in SEARCH_QUERIES:
            try:
                batch = await self._fetch_query(keyword, location, random.choice(_USER_AGENTS))
                jobs.extend(batch)
                logger.info("Indeed UK: %d jobs for '%s'", len(batch), keyword)
            except Exception as exc:
                logger.warning("Indeed UK query '%s' failed: %s", keyword, exc)

        return jobs

    async def _fetch_query(
        self, keyword: str, location: str, user_agent: str
    ) -> list[RawJob]:
        from urllib.parse import urlencode

        params = {"q": keyword, "sort": "date"}
        if location:
            params["l"] = location

        url = f"https://uk.indeed.com/jobs?{urlencode(params)}"
        resp = await self.get(url, headers={"User-Agent": user_agent, "Accept-Language": "en-GB,en;q=0.9"})
        soup = BeautifulSoup(resp.text, "lxml")

        jobs: list[RawJob] = []
        cards = soup.select("div.job_seen_beacon, div.tapItem")

        for card in cards:
            try:
                title_el = card.select_one("h2.jobTitle span[title], h2.jobTitle a span")
                company_el = card.select_one("span.companyName, [data-testid='company-name']")
                location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
                salary_el = card.select_one("div.salary-snippet-container, [data-testid='attribute_snippet_testid']")
                date_el = card.select_one("span.date, [data-testid='myJobsStateDate']")
                link_el = card.select_one("h2.jobTitle a")

                title = title_el.get_text(strip=True) if title_el else None
                company = company_el.get_text(strip=True) if company_el else None
                location = location_el.get_text(strip=True) if location_el else None

                if not title or not company:
                    continue

                href = link_el.get("href", "") if link_el else ""
                job_url = f"https://uk.indeed.com{href}" if href.startswith("/") else href

                salary_min, salary_max, currency = None, None, "GBP"
                if salary_el:
                    salary_text = salary_el.get_text(strip=True)
                    salary_min, salary_max, currency = _parse_salary_gbp(salary_text)

                posted_at = None
                if date_el:
                    posted_at = _parse_posted_date(date_el.get_text(strip=True))

                is_remote = bool(location and "remote" in location.lower())

                jobs.append(
                    RawJob(
                        title=title,
                        company=company,
                        location=location,
                        url=job_url,
                        source=self.source,
                        is_remote=is_remote,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        salary_currency=currency,
                        posted_at=posted_at,
                    )
                )
            except Exception:
                continue

        return jobs
