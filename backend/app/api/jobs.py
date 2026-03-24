from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ExperienceLevel, Job, JobType
from app.schemas import JobListResponse, JobListItem, JobRead, JobSearchParams
from app.search import search_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    is_remote: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all active jobs with optional basic filters."""
    stmt = select(Job).where(Job.is_active.is_(True))

    if source:
        stmt = stmt.where(Job.source == source)
    if is_remote is not None:
        stmt = stmt.where(Job.is_remote == is_remote)

    stmt = stmt.order_by(Job.posted_at.desc().nullslast(), Job.scraped_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Count
    from sqlalchemy import func, select as sel
    count_stmt = sel(func.count()).select_from(Job).where(Job.is_active.is_(True))
    if source:
        count_stmt = count_stmt.where(Job.source == source)
    if is_remote is not None:
        count_stmt = count_stmt.where(Job.is_remote == is_remote)
    total = (await db.execute(count_stmt)).scalar_one()

    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[JobListItem.model_validate(j) for j in jobs],
    )


@router.get("/search", response_model=JobListResponse)
async def search(
    q: Optional[str] = Query(None, description="Full-text search query"),
    location: Optional[str] = Query(None),
    job_type: Optional[JobType] = Query(None),
    experience_level: Optional[ExperienceLevel] = Query(None),
    is_remote: Optional[bool] = Query(None),
    is_hybrid: Optional[bool] = Query(None),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    source: Optional[str] = Query(None),
    days_ago: Optional[int] = Query(None, description="Jobs posted within N days"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Full-text search with filters, powered by Meilisearch.
    Falls back gracefully if Meilisearch is unavailable.
    """
    filters: list[str] = []

    if job_type:
        filters.append(f"job_type = {job_type.value}")
    if experience_level:
        filters.append(f"experience_level = {experience_level.value}")
    if is_remote is not None:
        filters.append(f"is_remote = {str(is_remote).lower()}")
    if is_hybrid is not None:
        filters.append(f"is_hybrid = {str(is_hybrid).lower()}")
    if salary_min is not None:
        filters.append(f"salary_min >= {salary_min}")
    if salary_max is not None:
        filters.append(f"salary_max <= {salary_max}")
    if source:
        filters.append(f"source = {source}")

    try:
        result = search_jobs(
            query=q,
            filters=filters or None,
            offset=(page - 1) * page_size,
            limit=page_size,
        )

        hits = result.get("hits", [])
        total = result.get("estimatedTotalHits", len(hits))

        # Filter by location client-side (Meilisearch doesn't geo-filter without coordinates)
        if location:
            loc_lower = location.lower()
            hits = [
                h for h in hits
                if h.get("location") and loc_lower in h["location"].lower()
            ]

        items = [
            JobListItem(
                id=h.get("hash", str(uuid.uuid4())),
                title=h["title"],
                company=h["company"],
                company_logo=h.get("company_logo"),
                location=h.get("location"),
                is_remote=h.get("is_remote", False),
                is_hybrid=h.get("is_hybrid", False),
                job_type=h.get("job_type"),
                experience_level=h.get("experience_level"),
                salary_min=h.get("salary_min"),
                salary_max=h.get("salary_max"),
                salary_currency=h.get("salary_currency"),
                skills=h.get("skills", []),
                posted_at=h.get("posted_at"),
                scraped_at=h.get("scraped_at"),
                source=h["source"],
                url=h["url"],
            )
            for h in hits
            if h.get("title") and h.get("company") and h.get("source") and h.get("url")
        ]

        return JobListResponse(total=total, page=page, page_size=page_size, items=items)

    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Search service unavailable: {exc}")


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a single job by its UUID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)
