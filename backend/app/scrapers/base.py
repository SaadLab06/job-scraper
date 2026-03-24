"""
Base scraper class.

Every scraper inherits from BaseScraper and implements `fetch_jobs()`.
The base class handles:
  - robots.txt compliance
  - rate limiting (configurable delay between requests)
  - exponential-backoff retry on HTTP errors
  - job normalization to the unified schema
  - SHA-256 deduplication hashing
  - DB upsert
  - Meilisearch index sync
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
import urllib.robotparser
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RawJob:
    """Intermediate representation produced by each scraper before normalization."""
    title: str
    company: str
    url: str
    source: str
    source_id: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    is_hybrid: bool = False
    job_type: Optional[str] = None          # raw string, will be normalized
    experience_level: Optional[str] = None  # raw string
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    posted_at: Optional[datetime] = None
    company_logo: Optional[str] = None


# Mapping of common raw job-type strings → canonical enum values
JOB_TYPE_MAP: dict[str, str] = {
    "full-time": "full_time",
    "full time": "full_time",
    "fulltime": "full_time",
    "part-time": "part_time",
    "part time": "part_time",
    "parttime": "part_time",
    "contract": "contract",
    "contractor": "contract",
    "freelance": "freelance",
    "internship": "internship",
    "intern": "internship",
}

EXPERIENCE_MAP: dict[str, str] = {
    "entry": "entry",
    "entry-level": "entry",
    "junior": "entry",
    "associate": "entry",
    "mid": "mid",
    "mid-level": "mid",
    "intermediate": "mid",
    "senior": "senior",
    "sr": "senior",
    "staff": "senior",
    "lead": "lead",
    "principal": "lead",
    "manager": "lead",
    "director": "lead",
}


def _normalize_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_hash(title: str, company: str, location: str) -> str:
    """SHA-256 of normalized title+company+location for cross-board dedup."""
    raw = f"{_normalize_text(title)}|{_normalize_text(company)}|{_normalize_text(location or '')}"
    return hashlib.sha256(raw.encode()).hexdigest()


class RobotsCache:
    """Simple in-process cache for parsed robots.txt files."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[urllib.robotparser.RobotFileParser, float]] = {}
        self._ttl = 3600  # re-fetch robots.txt after 1 hour

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        now = time.time()

        if base not in self._cache or (now - self._cache[base][1]) > self._ttl:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{base}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
            except Exception:
                # If robots.txt can't be fetched, assume allowed
                rp.allow_all = True
            self._cache[base] = (rp, now)

        rp, _ = self._cache[base]
        return rp.can_fetch(user_agent, url)


_robots_cache = RobotsCache()


class BaseScraper(ABC):
    """
    Abstract base class for all job board scrapers.

    Subclasses must implement `fetch_jobs()` which returns a list of RawJob.
    Everything else (dedup, upsert, search indexing) is handled here.
    """

    source: str = ""  # Override in subclass, e.g. "greenhouse"
    user_agent: str = "JobScraperBot/1.0 (+https://github.com/yourname/jobscraper)"
    request_delay: float = settings.scraper_request_delay_seconds
    max_retries: int = settings.scraper_max_retries
    timeout: int = settings.scraper_timeout_seconds

    def __init__(self) -> None:
        if not self.source:
            raise ValueError("Scraper subclass must define `source`")
        self._client: httpx.AsyncClient | None = None

    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        """Fetch raw job listings from the source. Must be implemented by subclass."""
        ...

    async def run(self) -> int:
        """
        Full scrape cycle:
        1. Fetch raw jobs
        2. Normalize + deduplicate
        3. Upsert to PostgreSQL
        4. Index in Meilisearch
        Returns count of upserted jobs.
        """
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
            proxies=settings.http_proxy,
            follow_redirects=True,
        ) as client:
            self._client = client
            raw_jobs = await self.fetch_jobs()

        normalized = [self._normalize(job) for job in raw_jobs if job]
        valid = [j for j in normalized if j is not None]

        upserted = await self._upsert_jobs(valid)
        await self._index_jobs(valid)

        logger.info(f"[{self.source}] {len(raw_jobs)} fetched → {len(valid)} valid → {upserted} upserted")
        return upserted

    def _normalize(self, raw: RawJob) -> dict | None:
        """Convert RawJob → dict matching the unified Job schema."""
        if not raw.title or not raw.company or not raw.url:
            return None

        job_type = JOB_TYPE_MAP.get(raw.job_type.lower().strip(), None) if raw.job_type else None
        exp_level = EXPERIENCE_MAP.get(raw.experience_level.lower().strip(), None) if raw.experience_level else None

        return {
            "source": self.source,
            "source_id": raw.source_id,
            "url": raw.url,
            "title": raw.title.strip(),
            "company": raw.company.strip(),
            "company_logo": raw.company_logo,
            "location": raw.location,
            "is_remote": raw.is_remote,
            "is_hybrid": raw.is_hybrid,
            "job_type": job_type,
            "experience_level": exp_level,
            "salary_min": raw.salary_min,
            "salary_max": raw.salary_max,
            "salary_currency": raw.salary_currency,
            "description": raw.description,
            "skills": raw.skills or [],
            "posted_at": raw.posted_at,
            "scraped_at": datetime.now(timezone.utc),
            "hash": compute_hash(raw.title, raw.company, raw.location or ""),
        }

    async def _upsert_jobs(self, jobs: list[dict]) -> int:
        """Upsert normalized jobs into PostgreSQL. On hash conflict, update scraped_at."""
        from app.database import AsyncSessionLocal
        from app.models import Job
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        if not jobs:
            return 0

        async with AsyncSessionLocal() as session:
            stmt = pg_insert(Job).values(jobs)
            stmt = stmt.on_conflict_do_update(
                index_elements=["hash"],
                set_={"scraped_at": stmt.excluded.scraped_at, "is_active": True},
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def _index_jobs(self, jobs: list[dict]) -> None:
        """Sync jobs to Meilisearch for fast search."""
        from app.search import get_search_client

        if not jobs:
            return
        try:
            client = get_search_client()
            index = client.index("jobs")
            # Convert UUIDs and datetimes to strings for Meilisearch
            docs = []
            for j in jobs:
                doc = {**j}
                doc["id"] = doc.get("hash")  # use hash as Meilisearch document id
                doc["scraped_at"] = doc["scraped_at"].isoformat() if doc.get("scraped_at") else None
                doc["posted_at"] = doc["posted_at"].isoformat() if doc.get("posted_at") else None
                docs.append(doc)
            index.add_documents(docs)
        except Exception as exc:
            logger.warning(f"Meilisearch indexing failed (non-fatal): {exc}")

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Rate-limited GET with robots.txt check and exponential backoff retry.
        """
        if not _robots_cache.is_allowed(url, self.user_agent):
            logger.warning(f"[{self.source}] robots.txt blocks {url}")
            raise PermissionError(f"robots.txt disallows {url}")

        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.request_delay)
                response = await self._client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 503):
                    wait = 2 ** attempt * 30  # 30s, 60s, 120s
                    logger.warning(f"[{self.source}] Rate limited on {url}, waiting {wait}s")
                    await asyncio.sleep(wait)
                elif exc.response.status_code in (403, 404):
                    raise
                else:
                    raise
            except httpx.RequestError as exc:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"[{self.source}] Request error (attempt {attempt+1}): {exc}")
                await asyncio.sleep(2 ** attempt * 5)

        raise RuntimeError(f"[{self.source}] Failed after {self.max_retries} attempts: {url}")
