"""
Emploitic scraper — largest job board in Algeria.
Scrapes public listing pages (French/Arabic bilingual site).
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
    "informatique",       # IT / computer science
    "developpeur",        # developer
    "ingenieur logiciel", # software engineer
    "data",
    "web",
    "mobile",
    "reseau",             # networking
]

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _parse_date(text: str) -> Optional[datetime]:
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    if "aujourd" in text or "today" in text:
        return now
    m = re.search(r"(\d+)\s*(jour|day|semaine|week|mois|month)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit in ("jour", "day"):
            return now - timedelta(days=n)
        if unit in ("semaine", "week"):
            return now - timedelta(weeks=n)
        if unit in ("mois", "month"):
            return now - timedelta(days=n * 30)
    return None


class EmploiticScraper(BaseScraper):
    source = "emploitic"

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        for keyword in SEARCH_QUERIES:
            try:
                batch = await self._fetch_query(keyword)
                jobs.extend(batch)
                logger.info("Emploitic: %d jobs for '%s'", len(batch), keyword)
            except Exception as exc:
                logger.warning("Emploitic query '%s' failed: %s", keyword, exc)
        return jobs

    async def _fetch_query(self, keyword: str) -> list[RawJob]:
        from urllib.parse import urlencode

        url = f"https://www.emploitic.com/offres-emploi?{urlencode({'q': keyword})}"
        resp = await self.get(url, headers={"User-Agent": _UA, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"})
        soup = BeautifulSoup(resp.text, "lxml")

        jobs: list[RawJob] = []

        # Emploitic uses article.job-offer or div.job-item style cards
        cards = soup.select("article.job-offer, div.job-item, li.offer-item")

        for card in cards:
            try:
                title_el = card.select_one("h2 a, h3 a, .job-title a, a.offer-title")
                company_el = card.select_one(".company-name, .employer-name, span.company")
                location_el = card.select_one(".job-location, .location, span.city")
                date_el = card.select_one(".posted-date, .date-posted, time, .job-date")
                link_el = title_el

                title = title_el.get_text(strip=True) if title_el else None
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc = location_el.get_text(strip=True) if location_el else "Algeria"

                if not title:
                    continue

                href = link_el.get("href", "") if link_el else ""
                if href.startswith("/"):
                    job_url = f"https://www.emploitic.com{href}"
                elif href.startswith("http"):
                    job_url = href
                else:
                    continue

                posted_at = None
                if date_el:
                    posted_at = _parse_date(date_el.get_text(strip=True))

                jobs.append(
                    RawJob(
                        title=title,
                        company=company,
                        location=loc,
                        url=job_url,
                        source=self.source,
                        is_remote=False,
                        posted_at=posted_at,
                    )
                )
            except Exception:
                continue

        return jobs
