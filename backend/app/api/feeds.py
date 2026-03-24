"""
RSS 2.0 feed endpoint — one feed per search query.

Usage:
  GET /api/v1/feeds/rss?q=python&location=remote&is_remote=true
  Returns: application/rss+xml
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Job
from app.search import search_jobs

router = APIRouter(tags=["feeds"])

_RSS_LIMIT = 50  # max items per feed


def _rfc2822(dt: Optional[datetime]) -> str:
    """Convert datetime to RFC 2822 string required by RSS pubDate."""
    if dt is None:
        return formatdate(usegmt=True)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return formatdate(dt.timestamp(), usegmt=True)


def _build_rss(
    title: str,
    description: str,
    link: str,
    jobs: list[Job],
    base_url: str,
) -> str:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "description").text = description
    ET.SubElement(channel, "link").text = link
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = _rfc2822(datetime.now(timezone.utc))

    for job in jobs:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"{job.title} — {job.company}"
        ET.SubElement(item, "link").text = f"{base_url}/jobs/{job.id}"
        ET.SubElement(item, "guid", isPermaLink="true").text = f"{base_url}/jobs/{job.id}"

        description_parts = [
            f"<strong>{job.company}</strong>",
            f"Location: {job.location or 'N/A'}",
        ]
        if job.is_remote:
            description_parts.append("✅ Remote")
        if job.salary_min or job.salary_max:
            salary = f"{job.salary_min or '?'} – {job.salary_max or '?'} {job.salary_currency or 'USD'}"
            description_parts.append(f"Salary: {salary}")
        description_parts.append(f'<a href="{job.url}">Apply on {job.source}</a>')
        ET.SubElement(item, "description").text = "<br/>".join(description_parts)

        ET.SubElement(item, "pubDate").text = _rfc2822(job.posted_at)
        ET.SubElement(item, "author").text = job.company
        ET.SubElement(item, "category").text = job.source

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")


@router.get("/feeds/rss")
async def rss_feed(
    q: Optional[str] = Query(None, description="Search keyword"),
    location: Optional[str] = Query(None),
    is_remote: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Returns an RSS 2.0 feed for any search query.
    Subscribe in your RSS reader: /api/v1/feeds/rss?q=python&is_remote=true
    """
    # Use Meilisearch if keyword is provided, fallback to DB otherwise
    if q:
        filters = []
        if location:
            filters.append(f'location CONTAINS "{location}"')
        if is_remote is True:
            filters.append("is_remote = true")
        if source:
            filters.append(f'source = "{source}"')

        result = search_jobs(
            query=q,
            filter_str=" AND ".join(filters) if filters else None,
            limit=_RSS_LIMIT,
        )
        job_ids = [hit["id"] for hit in result.get("hits", [])]

        if job_ids:
            stmt = select(Job).where(Job.id.in_(job_ids), Job.is_active.is_(True))
            rows = await db.execute(stmt)
            jobs = list(rows.scalars().all())
            # Preserve Meilisearch relevance order
            id_to_job = {str(j.id): j for j in jobs}
            jobs = [id_to_job[jid] for jid in job_ids if jid in id_to_job]
        else:
            jobs = []
    else:
        stmt = (
            select(Job)
            .where(Job.is_active.is_(True))
            .order_by(Job.posted_at.desc().nullslast())
            .limit(_RSS_LIMIT)
        )
        if is_remote is True:
            stmt = stmt.where(Job.is_remote.is_(True))
        if source:
            stmt = stmt.where(Job.source == source)
        rows = await db.execute(stmt)
        jobs = list(rows.scalars().all())

    feed_title = f"JobScraper: {q or 'Latest Jobs'}"
    if location:
        feed_title += f" in {location}"
    feed_description = (
        f"Latest job listings matching '{q}' from JobScraper" if q
        else "Latest job listings from JobScraper"
    )

    # Build absolute base URL — in production, set BASE_URL in environment
    from app.config import settings

    base_url = settings.base_url.rstrip("/")
    feed_link = f"{base_url}/jobs"
    if q:
        feed_link += f"?q={q}"

    xml_content = _build_rss(
        title=feed_title,
        description=feed_description,
        link=feed_link,
        jobs=jobs,
        base_url=base_url,
    )

    return Response(
        content=xml_content,
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )
