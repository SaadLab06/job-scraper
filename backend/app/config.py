from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/jobscraper"
    redis_url: str = "redis://localhost:6379/0"
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: str = "masterKey"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    from_email: str = "alerts@jobscraper.local"
    secret_key: str = "change-me"
    admin_token: str = "change-me-admin"
    scraper_request_delay_seconds: float = 2.0
    scraper_max_retries: int = 3
    scraper_timeout_seconds: int = 30
    http_proxy: str | None = None
    base_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
