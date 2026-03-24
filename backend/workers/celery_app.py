from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "jobscraper",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry configuration
    task_max_retries=3,
    task_default_retry_delay=60,
)

# Periodic scraping schedule
celery_app.conf.beat_schedule = {
    # High-frequency sources: every 4 hours
    "scrape-greenhouse": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=0, hour="*/4"),
        "args": ("greenhouse",),
    },
    "scrape-lever": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=15, hour="*/4"),
        "args": ("lever",),
    },
    # Standard frequency: every 6 hours
    "scrape-indeed": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=30, hour="*/6"),
        "args": ("indeed",),
    },
    # Phase 2: additional boards — every 8 hours (more conservative)
    # LinkedIn: twice daily max — respect rate limits and ToS
    "scrape-linkedin": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=45, hour="*/12"),
        "args": ("linkedin",),
    },
    "scrape-indeed-uk": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=0, hour="*/8"),
        "args": ("indeed_uk",),
    },
    "scrape-bayt": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=20, hour="*/8"),
        "args": ("bayt",),
    },
    "scrape-emploitic": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=40, hour="*/12"),
        "args": ("emploitic",),
    },
    "scrape-rekrute": {
        "task": "workers.tasks.run_scraper",
        "schedule": crontab(minute=0, hour="*/12"),
        "args": ("rekrute",),
    },
    # Daily job expiry cleanup
    "expire-old-jobs": {
        "task": "workers.tasks.expire_old_jobs",
        "schedule": crontab(hour=2, minute=0),
    },
    # Daily alert digest
    "send-daily-alerts": {
        "task": "workers.tasks.send_alert_digests",
        "schedule": crontab(hour=7, minute=0),
        "args": ("daily",),
    },
    "send-weekly-alerts": {
        "task": "workers.tasks.send_alert_digests",
        "schedule": crontab(hour=7, minute=0, day_of_week=1),
        "args": ("weekly",),
    },
}
