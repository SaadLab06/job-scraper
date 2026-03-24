"""
JobScraper FastAPI application entry point.

API base: /api/v1
Docs: /docs (Swagger UI), /redoc
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jobs import router as jobs_router
from app.api.alerts import router as alerts_router
from app.api.feeds import router as feeds_router
from app.search import configure_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JobScraper API",
    description="Multi-region job aggregation API — Every job. One place. Always fresh.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(feeds_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    logger.info("JobScraper API starting up...")
    try:
        configure_index()
    except Exception as exc:
        logger.warning(f"Meilisearch config failed (will retry on next request): {exc}")


@app.get("/", tags=["health"])
async def root():
    return {"service": "JobScraper API", "version": "1.0.0", "status": "ok"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
