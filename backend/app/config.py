"""Application configuration.

All secrets and environment-specific values are read from environment variables
(or a local .env file) — never hard-coded. See the repo-root .env.example for the
full list of supported variables.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "Social Cook API"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"

    # --- Database (Phase 2+) ---
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/social_cook"
    )

    # --- Auth (Phase 2+) ---
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 43200  # 30 days

    # --- AI: structuring + vision (Anthropic) ---
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"

    # --- AI: transcription (pluggable; OpenAI Whisper default) ---
    openai_api_key: str | None = None
    whisper_model: str = "whisper-1"

    # --- Monetization (Phase 5+) ---
    revenuecat_api_key: str | None = None
    revenuecat_webhook_auth: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the .env file is parsed only once."""
    return Settings()
