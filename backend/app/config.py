"""
Centralized application configuration.

We use pydantic-settings so every config value is:
  - typed (fails fast at startup if misconfigured, not at request time)
  - documented in one place
  - overridable via environment variables / .env file

Never import os.environ directly elsewhere in the app — always go through `settings`.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "URL Shortener API"
    environment: str = "development"  # development | staging | production
    debug: bool = True

    # --- Database ---
    database_url: str = "postgresql://postgres:postgres@localhost:5432/urlshortener"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl_seconds: int = 3600  # how long a short_code -> url mapping lives in cache

    # --- Auth (JWT) ---
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Short URL ---
    short_code_length: int = 7
    base_redirect_url: str = "http://localhost:8000"  # used to build the full short URL returned to clients

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we parse env vars once per process, not on every request.
    FastAPI's dependency injection will call this repeatedly — lru_cache makes it cheap.
    """
    return Settings()


settings = get_settings()
