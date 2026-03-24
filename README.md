# JobScraper

> **Every job. One place. Always fresh.**

An open-source, self-hostable job aggregation platform. Scrapes 10 job boards, deduplicates listings, and delivers a unified search + alert experience — all via Docker Compose in one command.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

---

## Features

- **10 job boards** scraped out of the box — Greenhouse, Lever, Indeed, Indeed UK, LinkedIn, Bayt, Emploitic, Rekrute, and more
- **Full-text search** powered by Meilisearch — instant results with typo tolerance
- **Smart deduplication** — content-hash fingerprinting prevents duplicate listings
- **Email alerts** — subscribe to any search query; double opt-in, one-click unsubscribe
- **RSS feeds** — subscribe to any search in your RSS reader
- **Pluggable scrapers** — add a new board in ~15 lines of Python
- **Salary, location, remote, job-type filters**
- **Next.js frontend** with saved jobs (localStorage) and alert management
- **Celery + Beat scheduler** — scraping runs automatically on a configurable schedule

---

## Quick Start (Docker Compose)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/jobscraper.git
cd jobscraper

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — change SECRET_KEY and ADMIN_TOKEN at minimum

# 3. Start all services
docker-compose up -d

# 4. Run database migrations
docker-compose exec api alembic upgrade head

# 5. Trigger your first scrape
docker-compose exec worker celery -A workers.celery_app call workers.tasks.run_scraper --args='["greenhouse"]'
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |
| Meilisearch Dashboard | http://localhost:7700 |
| MailHog (email preview) | http://localhost:8025 |

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────────┐
│  Beat       │────▶│  Celery      │────▶│  Scrapers (pluggable)    │
│  Scheduler  │     │  Workers     │     │  greenhouse / lever /    │
└─────────────┘     └──────────────┘     │  indeed / linkedin /     │
                                         │  bayt / emploitic / ...  │
                                         └────────────┬─────────────┘
                                                      │
                              ┌───────────────────────▼──────────┐
                              │  Normalizer + Deduplicator        │
                              │  (content-hash fingerprinting)    │
                              └──────────┬────────────┬───────────┘
                                         │            │
                                  ┌──────▼──┐  ┌──────▼──────┐
                                  │Postgres │  │Meilisearch  │
                                  └──────┬──┘  └──────┬──────┘
                                         │            │
                              ┌──────────▼────────────▼────────┐
                              │         FastAPI                  │
                              │  /api/v1/jobs  /api/v1/alerts   │
                              │  /api/v1/feeds/rss              │
                              └─────────────────────────────────┘
                                              │
                              ┌───────────────▼────────────────┐
                              │       Next.js 14 Frontend       │
                              │  Search · Filters · Saved Jobs  │
                              │  Job Detail · Email Alerts      │
                              └────────────────────────────────┘
```

---

## Supported Job Boards

| Source | Method | Status |
|--------|--------|--------|
| Greenhouse | REST API | ✅ Live |
| Lever | REST API | ✅ Live |
| Indeed (US) | HTML scraping | ✅ Live |
| Indeed UK | HTML scraping | ✅ Live |
| LinkedIn | HTML scraping | ✅ Live |
| Bayt | HTML scraping | ✅ Live |
| Emploitic | HTML scraping | ✅ Live |
| Rekrute | HTML scraping | ✅ Live |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.115 + Python 3.12 |
| Database | PostgreSQL 16 (SQLAlchemy async + Alembic) |
| Search | Meilisearch v1.12 |
| Task queue | Celery 5.4 + Redis 7 |
| Scraping | httpx + BeautifulSoup4 + Playwright |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Email | Resend / MailHog (local dev) |
| Deploy | Docker Compose (single command) |

---

## API Reference

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs` | List all active jobs (paginated) — filters: `source`, `is_remote` |
| `GET` | `/api/v1/jobs/search` | Full-text search with filters (see below) |
| `GET` | `/api/v1/jobs/{id}` | Get full job detail by UUID |

**Search query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text keyword |
| `location` | string | Location substring match |
| `job_type` | enum | `full_time` `part_time` `contract` `internship` |
| `experience_level` | enum | `entry` `mid` `senior` `lead` |
| `is_remote` | bool | Remote jobs only |
| `is_hybrid` | bool | Hybrid jobs only |
| `salary_min` | float | Minimum salary |
| `salary_max` | float | Maximum salary |
| `source` | string | Filter by board name |
| `days_ago` | int | Posted within N days |
| `page` / `page_size` | int | Pagination (default 20, max 100) |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/alerts` | Subscribe to a search query (sends confirmation email) |
| `GET` | `/api/v1/alerts/confirm/{token}` | Double opt-in confirmation |
| `DELETE` | `/api/v1/alerts/{id}` | Unsubscribe |

### Feeds

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/feeds/rss` | RSS 2.0 feed for any search query |

Example: `GET /api/v1/feeds/rss?q=python+developer&is_remote=true`

Full interactive docs: **http://localhost:8000/docs**

---

## Adding a New Scraper

Create `backend/app/scrapers/myboard.py`:

```python
from app.scrapers.base import BaseScraper, RawJob

class MyBoardScraper(BaseScraper):
    source = "myboard"

    async def fetch_jobs(self) -> list[RawJob]:
        response = await self.get("https://myboard.com/jobs.json")
        return [
            RawJob(
                title=item["title"],
                company=item["company"],
                url=item["url"],
                source=self.source,
            )
            for item in response.json()
        ]
```

Register it in `backend/workers/tasks.py`:

```python
SCRAPER_REGISTRY["myboard"] = "app.scrapers.myboard.MyBoardScraper"
```

Add a beat schedule in `backend/workers/celery_app.py`. Done.

---

## Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Requires Postgres + Redis + Meilisearch (run infra only via Docker)
docker-compose up -d postgres redis meilisearch mailhog

# Run API
uvicorn app.main:app --reload

# Run Celery worker
celery -A workers.celery_app worker --loglevel=info

# Run migrations
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev    # http://localhost:3000
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and update:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://... | PostgreSQL connection string |
| `REDIS_URL` | redis://... | Redis connection string |
| `MEILISEARCH_URL` | http://localhost:7700 | Meilisearch host |
| `MEILISEARCH_API_KEY` | masterKey | Meilisearch master key |
| `SECRET_KEY` | change-me | App secret (change in production) |
| `ADMIN_TOKEN` | change-me | Admin API token |
| `SMTP_HOST` | localhost | SMTP server (MailHog in dev) |
| `FROM_EMAIL` | alerts@... | Sender address for alert emails |
| `BASE_URL` | http://localhost:3000 | Public base URL (used in emails + RSS) |
| `SCRAPER_REQUEST_DELAY_SECONDS` | 2 | Delay between scraper requests |

---

## Project Structure

```
jobscraper/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers
│   │   ├── scrapers/      # One file per job board
│   │   ├── services/      # Alert delivery logic
│   │   ├── models.py      # SQLAlchemy ORM models
│   │   ├── schemas.py     # Pydantic request/response schemas
│   │   ├── search.py      # Meilisearch client + index config
│   │   ├── config.py      # Settings (pydantic-settings)
│   │   └── main.py        # FastAPI app entry point
│   ├── workers/
│   │   ├── celery_app.py  # Celery app + beat schedule
│   │   └── tasks.py       # Scraper task definitions
│   ├── alembic/           # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # Reusable UI components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # API client + types + utilities
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## License

[MIT](LICENSE)
