import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import update

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Registry mapping source name → scraper class
SCRAPER_REGISTRY: dict[str, str] = {
    # Phase 1 — API-based
    "greenhouse": "app.scrapers.greenhouse.GreenhouseScraper",
    "lever": "app.scrapers.lever.LeverScraper",
    # Phase 1 — HTML
    "indeed": "app.scrapers.indeed.IndeedScraper",
    # Phase 2 — additional boards
    "linkedin": "app.scrapers.linkedin.LinkedInScraper",
    "indeed_uk": "app.scrapers.indeed_uk.IndeedUKScraper",
    "bayt": "app.scrapers.bayt.BaytScraper",
    "emploitic": "app.scrapers.emploitic.EmploiticScraper",
    "rekrute": "app.scrapers.rekrute.RekruteScraper",
}


def _import_scraper(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@celery_app.task(bind=True, name="workers.tasks.run_scraper", max_retries=3)
def run_scraper(self, source: str, **kwargs):
    """Run a named scraper and ingest results into the DB."""
    if source not in SCRAPER_REGISTRY:
        raise ValueError(f"Unknown scraper source: {source}")

    logger.info(f"Starting scraper: {source}")
    try:
        scraper_cls = _import_scraper(SCRAPER_REGISTRY[source])
        scraper = scraper_cls()
        count = asyncio.run(scraper.run())
        logger.info(f"Scraper '{source}' completed: {count} jobs upserted")
        return {"source": source, "jobs_upserted": count}
    except Exception as exc:
        logger.error(f"Scraper '{source}' failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="workers.tasks.expire_old_jobs")
def expire_old_jobs(days: int = 14):
    """Mark jobs not seen in `days` days as inactive."""
    async def _expire():
        from app.database import AsyncSessionLocal
        from app.models import Job

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(Job)
                .where(Job.scraped_at < cutoff, Job.is_active.is_(True))
                .values(is_active=False)
                .returning(Job.id)
            )
            expired = result.rowcount
            await session.commit()
            logger.info(f"Expired {expired} old jobs (older than {days} days)")
            return expired

    return asyncio.run(_expire())


@celery_app.task(name="workers.tasks.send_alert_digests")
def send_alert_digests(frequency: str = "daily"):
    """Find active alerts matching `frequency` and send email digests."""
    async def _send():
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import select

        from app.database import AsyncSessionLocal
        from app.models import Alert, Job
        from app.search import search_jobs
        from app.services.alerts import send_digest_email

        window_hours = {"realtime": 1, "daily": 24, "weekly": 168}.get(frequency, 24)
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Alert).where(
                    Alert.frequency == frequency,
                    Alert.is_active.is_(True),
                    Alert.confirmed.is_(True),
                )
            )
            alerts = result.scalars().all()
            logger.info(f"Sending {frequency} digest to {len(alerts)} subscribers")

            sent = 0
            for alert in alerts:
                try:
                    search_result = search_jobs(query=alert.query, limit=10)
                    hit_ids = [h.get("id") for h in search_result.get("hits", []) if h.get("id")]
                    if not hit_ids:
                        continue

                    jobs_result = await session.execute(
                        select(Job).where(
                            Job.id.in_(hit_ids),
                            Job.is_active.is_(True),
                            Job.scraped_at >= since,
                        )
                    )
                    jobs = jobs_result.scalars().all()
                    if jobs:
                        send_digest_email(alert, jobs)
                        sent += 1
                except Exception as exc:
                    logger.warning(f"Digest failed for alert {alert.id}: {exc}")

            logger.info(f"Digest sent to {sent}/{len(alerts)} subscribers")
            return sent

    return asyncio.run(_send())
