"""
Meilisearch client and index configuration.

The 'jobs' index is configured with:
  - Searchable attributes (title, company, location, description, skills)
  - Filterable attributes (for sidebar filters)
  - Sortable attributes (posted_at, scraped_at)
  - Ranking rules optimized for job search
"""

import logging

import meilisearch

from app.config import settings

logger = logging.getLogger(__name__)

_client: meilisearch.Client | None = None


def get_search_client() -> meilisearch.Client:
    global _client
    if _client is None:
        _client = meilisearch.Client(settings.meilisearch_url, settings.meilisearch_api_key)
    return _client


def configure_index() -> None:
    """
    Set up Meilisearch index settings.
    Call once at app startup or after creating the index.
    """
    client = get_search_client()
    index = client.index("jobs")

    index.update_searchable_attributes([
        "title",
        "company",
        "location",
        "description",
        "skills",
    ])

    index.update_filterable_attributes([
        "source",
        "job_type",
        "experience_level",
        "is_remote",
        "is_hybrid",
        "salary_min",
        "salary_max",
        "salary_currency",
        "is_active",
    ])

    index.update_sortable_attributes([
        "posted_at",
        "scraped_at",
        "salary_min",
        "salary_max",
    ])

    index.update_ranking_rules([
        "words",
        "typo",
        "proximity",
        "attribute",
        "sort",
        "exactness",
    ])

    logger.info("Meilisearch 'jobs' index configured")


def search_jobs(
    query: str | None = None,
    filters: list[str] | None = None,
    sort: list[str] | None = None,
    offset: int = 0,
    limit: int = 20,
) -> dict:
    """
    Execute a search against the jobs index.

    Returns a dict with keys: hits, totalHits, offset, limit.
    """
    client = get_search_client()
    index = client.index("jobs")

    search_params: dict = {
        "offset": offset,
        "limit": limit,
        "attributesToRetrieve": [
            "id", "title", "company", "company_logo", "location",
            "is_remote", "is_hybrid", "job_type", "experience_level",
            "salary_min", "salary_max", "salary_currency",
            "skills", "posted_at", "scraped_at", "source", "url", "hash",
        ],
    }

    if filters:
        search_params["filter"] = filters

    if sort:
        search_params["sort"] = sort
    else:
        search_params["sort"] = ["posted_at:desc"]

    # Active jobs only
    active_filter = "is_active = true"
    if search_params.get("filter"):
        if isinstance(search_params["filter"], list):
            search_params["filter"].append(active_filter)
        else:
            search_params["filter"] = [search_params["filter"], active_filter]
    else:
        search_params["filter"] = [active_filter]

    result = index.search(query or "", search_params)
    return result
