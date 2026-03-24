from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from app.models import ExperienceLevel, JobType


class JobBase(BaseModel):
    title: str
    company: str
    company_logo: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_remote: bool = False
    is_hybrid: bool = False
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    skills: list[str] = []
    posted_at: Optional[datetime] = None
    source: str
    url: str


class JobRead(JobBase):
    id: uuid.UUID
    scraped_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    company_logo: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool
    is_hybrid: bool
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    skills: list[str] = []
    posted_at: Optional[datetime] = None
    scraped_at: datetime
    source: str
    url: str

    model_config = {"from_attributes": True}


class JobSearchParams(BaseModel):
    q: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    is_remote: Optional[bool] = None
    is_hybrid: Optional[bool] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    source: Optional[str] = None
    days_ago: Optional[int] = None  # posted within N days
    page: int = 1
    page_size: int = 20


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[JobListItem]


class AlertCreate(BaseModel):
    email: str
    query: str
    filters: Optional[str] = None
    frequency: str = "daily"


class AlertRead(BaseModel):
    id: uuid.UUID
    email: str
    query: str
    frequency: str
    is_active: bool
    confirmed: bool

    model_config = {"from_attributes": True}
