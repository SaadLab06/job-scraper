"""
Indeed public job search HTML scraper.

Indeed blocks aggressive scrapers. This implementation:
  - Respects robots.txt (checked by base class)
  - Uses randomized delays between requests
  - Rotates User-Agent strings
  - Supports configurable search queries and locations

NOTE: For production at scale, consider the Indeed Publisher API
(https://developer.indeed.com/) as a legal alternative.

This scraper targets the public HTML search results page.
"""

from __future__ import annotations

import logging
import random
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# Search queries to run — (query, location) pairs
INDEED_SEARCHES: list[tuple[str, str]] = [
    ("software engineer", "remote"),
    ("python developer", "remote"),
    ("frontend engineer", "remote"),
    ("data scientist", "remote"),
    ("backend engineer", "remote"),
    ("devops engineer", "remote"),
    ("machine learning engineer", "remote"),
]

INDEED_BASE_URL = "https://www.indeed.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


def _parse_relative_date(text: str) -> datetime | None:
    """Convert 'Posted 3 days ago' → datetime."""
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    if "just posted" in text or "today" in text:
        return now
    match = re.search(r"(\d+)\s*(hour|day|week|month)", text)
    if not match:
        return None
    n, unit = int(match.group(1)), match.group(2)
    if unit == "hour":
        return now - timedelta(hours=n)
    if unit == "day":
        return now - timedelta(days=n)
    if unit == "week":
        return now - timedelta(weeks=n)
    if unit == "month":
        return now - timedelta(days=n * 30)
    return None


class IndeedScraper(BaseScraper):
    source = "indeed"
    # Longer delay to be respectful with HTML scraping
    request_delay: float = 4.0

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen_ids: set[str] = set()

        for query, location in INDEED_SEARCHES:
            try:
                page_jobs = await self._fetch_search(query, location, seen_ids)
                jobs.extend(page_jobs)
            except PermissionError:
                logger.warning(f"[indeed] robots.txt blocked search: {query} in {location}")
                continue
            except Exception as exc:
                logger.error(f"[indeed] Search failed ({query}, {location}): {exc}")
                continue

        return jobs

    async def _fetch_search(
        self, query: str, location: str, seen_ids: set[str]
    ) -> list[RawJob]:
        params = {
            "q": query,
            "l": location,
            "fromage": "14",  # last 14 days
            "sort": "date",
        }
        url = f"{INDEED_BASE_URL}/jobs?{urlencode(params)}"

        # Rotate user-agent per request
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        response = await self._client.get(
            url,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        if response.status_code != 200:
            logger.warning(f"[indeed] HTTP {response.status_code} for {url}")
            return []

        return self._parse_results_page(response.text, seen_ids)

    def _parse_results_page(self, html: str, seen_ids: set[str]) -> list[RawJob]:
        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJob] = []

        # Indeed job cards use data-jk attribute as the job key
        job_cards = soup.find_all("div", attrs={"data-jk": True})

        for card in job_cards:
            try:
                job_id = card.get("data-jk", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title_el = card.find("h2", class_=re.compile(r"jobTitle"))
                title = title_el.get_text(strip=True) if title_el else None
                if not title:
                    continue

                company_el = card.find("span", attrs={"data-testid": "company-name"})
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                location_el = card.find("div", attrs={"data-testid": "text-location"})
                location = location_el.get_text(strip=True) if location_el else None

                salary_el = card.find("div", attrs={"data-testid": "attribute_snippet_testid"})
                salary_text = salary_el.get_text(strip=True) if salary_el else ""
                salary_min, salary_max, salary_currency = self._parse_salary(salary_text)

                date_el = card.find("span", attrs={"data-testid": "myJobsStateDate"})
                posted_at = _parse_relative_date(date_el.get_text()) if date_el else None

                is_remote = location and "remote" in location.lower()

                job_url = f"{INDEED_BASE_URL}/viewjob?jk={job_id}"

                jobs.append(RawJob(
                    title=title,
                    company=company,
                    url=job_url,
                    source=self.source,
                    source_id=job_id,
                    location=location,
                    is_remote=bool(is_remote),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=salary_currency,
                    posted_at=posted_at,
                ))
            except Exception as exc:
                logger.debug(f"[indeed] Failed to parse card: {exc}")
                continue

        logger.info(f"[indeed] Parsed {len(jobs)} jobs from page")
        return jobs

    @staticmethod
    def _parse_salary(text: str) -> tuple[float | None, float | None, str | None]:
        """Extract salary range from text like '$80,000 - $120,000 a year'."""
        if not text:
            return None, None, None

        currency = "USD" if "$" in text else ("GBP" if "£" in text else None)
        numbers = re.findall(r"[\d,]+", text.replace("$", "").replace("£", ""))
        numbers = [float(n.replace(",", "")) for n in numbers if n]

        if len(numbers) >= 2:
            # If hourly, rough annual estimate: × 2080
            if "hour" in text.lower():
                return numbers[0] * 2080, numbers[1] * 2080, currency
            return numbers[0], numbers[1], currency
        if len(numbers) == 1:
            return numbers[0], None, currency
        return None, None, None
