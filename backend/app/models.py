import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, Index,
    String, Text, ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

import enum


class JobType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    freelance = "freelance"
    internship = "internship"


class ExperienceLevel(str, enum.Enum):
    entry = "entry"
    mid = "mid"
    senior = "senior"
    lead = "lead"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source tracking
    source = Column(String(64), nullable=False, index=True)
    source_id = Column(String(256), nullable=True)
    url = Column(Text, nullable=False)

    # Core job fields
    title = Column(String(512), nullable=False)
    company = Column(String(256), nullable=False)
    company_logo = Column(Text, nullable=True)
    location = Column(String(256), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Work mode
    is_remote = Column(Boolean, default=False)
    is_hybrid = Column(Boolean, default=False)

    # Classification
    job_type = Column(Enum(JobType), nullable=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=True)

    # Compensation
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(8), nullable=True)

    # Content
    description = Column(Text, nullable=True)
    skills = Column(ARRAY(String), nullable=True, default=list)

    # Timestamps
    posted_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Deduplication & lifecycle
    hash = Column(String(64), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)

    __table_args__ = (
        Index("ix_jobs_source_active", "source", "is_active"),
        Index("ix_jobs_posted_at", "posted_at"),
        Index("ix_jobs_company", "company"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(256), nullable=False, index=True)
    query = Column(String(512), nullable=False)
    filters = Column(Text, nullable=True)  # JSON-encoded filter state
    frequency = Column(String(16), default="daily")  # realtime | daily | weekly
    is_active = Column(Boolean, default=True)
    confirmed = Column(Boolean, default=False)
    confirm_token = Column(String(128), nullable=True, unique=True)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
