"""
Lever Job Posting API scraper.

Lever provides a public REST API at:
  https://api.lever.co/v0/postings/{company_slug}?mode=json

Returns structured JSON — no HTML scraping needed.
No authentication required.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

LEVER_COMPANIES: list[str] = [
    "netflix",
    "spotify",
    "coinbase",
    "square",
    "postman",
    "discord",
    "canva",
    "asana",
    "hashicorp",
    "cloudflare",
    "brex",
    "deel",
    "rippling",
    "retool",
    "scale",
]

LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"


class LeverScraper(BaseScraper):
    source = "lever"

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []

        for slug in LEVER_COMPANIES:
            try:
                url = LEVER_API.format(slug=slug)
                response = await self.get(url)
                items = response.json()

                if not isinstance(items, list):
                    logger.warning(f"[lever] Unexpected response for {slug}")
                    continue

                logger.info(f"[lever] {slug}: {len(items)} jobs")
                for item in items:
                    raw = self._parse_job(item, slug)
                    if raw:
                        jobs.append(raw)
            except Exception as exc:
                logger.error(f"[lever] Failed for {slug}: {exc}")
                continue

        return jobs

    def _parse_job(self, item: dict, slug: str) -> RawJob | None:
        try:
            title = item.get("text", "").strip()
            if not title:
                return None

            categories = item.get("categories", {})
            location = categories.get("location", "")
            team = categories.get("team", "")
            commitment = categories.get("commitment", "")  # Full-time, Part-time, etc.

            is_remote = "remote" in location.lower() if location else False

            # Salary from tags (Lever posts sometimes include salary tags)
            salary_min = salary_max = None
            salary_currency = "USD"
            tags = item.get("tags", [])

            # Posted date from createdAt (epoch ms)
            posted_at = None
            created_at_ms = item.get("createdAt")
            if created_at_ms:
                posted_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)

            description_lists = item.get("lists", [])
            description_text = item.get("descriptionPlain", "") or ""
            if description_lists:
                for section in description_lists:
                    description_text += f"\n{section.get('text', '')}\n"
                    for content in section.get("content", []):
                        description_text += f"• {content}\n"

            skills = [t for t in tags if t]

            return RawJob(
                title=title,
                company=slug.replace("-", " ").title(),
                url=item.get("hostedUrl", f"https://jobs.lever.co/{slug}/{item.get('id', '')}"),
                source=self.source,
                source_id=item.get("id"),
                location=location or None,
                is_remote=is_remote,
                job_type=commitment or None,
                description=description_text.strip() or None,
                skills=skills,
                posted_at=posted_at,
            )
        except Exception as exc:
            logger.warning(f"[lever] Failed to parse job for {slug}: {exc}")
            return None
