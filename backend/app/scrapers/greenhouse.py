"""
Greenhouse Job Board API scraper.

Greenhouse provides a public REST API at:
  https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true

This scraper fetches jobs from a configurable list of company slugs.
No authentication required — all data is publicly available.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# Extend this list to add more companies using Greenhouse ATS
GREENHOUSE_COMPANIES: list[str] = [
    "anthropic",
    "stripe",
    "figma",
    "notion",
    "linear",
    "vercel",
    "planetscale",
    "supabase",
    "airbnb",
    "dropbox",
    "github",
    "shopify",
    "atlassian",
    "twilio",
    "datadog",
]

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


class GreenhouseScraper(BaseScraper):
    source = "greenhouse"

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []

        for slug in GREENHOUSE_COMPANIES:
            try:
                url = f"{GREENHOUSE_API.format(slug=slug)}?content=true"
                response = await self.get(url)
                data = response.json()
                company_jobs = data.get("jobs", [])
                logger.info(f"[greenhouse] {slug}: {len(company_jobs)} jobs")

                for item in company_jobs:
                    raw = self._parse_job(item, slug)
                    if raw:
                        jobs.append(raw)
            except Exception as exc:
                logger.error(f"[greenhouse] Failed for {slug}: {exc}")
                continue

        return jobs

    def _parse_job(self, item: dict, slug: str) -> RawJob | None:
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            # Location
            offices = item.get("offices", [])
            location = offices[0].get("name") if offices else None
            is_remote = any(
                "remote" in (o.get("name", "")).lower() for o in offices
            )

            # Posted date
            posted_at = None
            updated_at_str = item.get("updated_at")
            if updated_at_str:
                try:
                    posted_at = datetime.fromisoformat(
                        updated_at_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            # Description (HTML — stripped for now)
            description = item.get("content", "")

            # Departments as skills/tags
            departments = item.get("departments", [])
            skills = [d.get("name", "") for d in departments if d.get("name")]

            return RawJob(
                title=title,
                company=slug.replace("-", " ").title(),
                url=item.get("absolute_url", f"https://boards.greenhouse.io/{slug}/jobs/{item['id']}"),
                source=self.source,
                source_id=str(item.get("id")),
                location=location,
                is_remote=is_remote,
                description=description,
                skills=skills,
                posted_at=posted_at,
            )
        except Exception as exc:
            logger.warning(f"[greenhouse] Failed to parse job: {exc}")
            return None
