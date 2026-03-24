"""Initial schema: jobs and alerts tables

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(256), nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(256), nullable=False),
        sa.Column("company_logo", sa.Text, nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("is_remote", sa.Boolean, default=False),
        sa.Column("is_hybrid", sa.Boolean, default=False),
        sa.Column("job_type", sa.Enum(
            "full_time", "part_time", "contract", "freelance", "internship",
            name="jobtype"
        ), nullable=True),
        sa.Column("experience_level", sa.Enum(
            "entry", "mid", "senior", "lead",
            name="experiencelevel"
        ), nullable=True),
        sa.Column("salary_min", sa.Float, nullable=True),
        sa.Column("salary_max", sa.Float, nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("hash", sa.String(64), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
    )
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_hash", "jobs", ["hash"], unique=True)
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"])
    op.create_index("ix_jobs_source_active", "jobs", ["source", "is_active"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])
    op.create_index("ix_jobs_company", "jobs", ["company"])

    # Full-text search index on title + company
    op.execute("""
        ALTER TABLE jobs
        ADD COLUMN fts tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(company, '') || ' ' || coalesce(location, ''))
        ) STORED
    """)
    op.execute("CREATE INDEX ix_jobs_fts ON jobs USING gin(fts)")

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("query", sa.String(512), nullable=False),
        sa.Column("filters", sa.Text, nullable=True),
        sa.Column("frequency", sa.String(16), default="daily"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("confirmed", sa.Boolean, default=False),
        sa.Column("confirm_token", sa.String(128), nullable=True, unique=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_alerts_email", "alerts", ["email"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_index("ix_jobs_fts", "jobs")
    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS jobtype")
    op.execute("DROP TYPE IF EXISTS experiencelevel")
