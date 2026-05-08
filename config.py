"""
Centralized application configuration using Pydantic Settings.
All environment variables are validated and typed here — single source of truth.
"""
from __future__ import annotations
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Google AI ──────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")

    # ── Google Maps ────────────────────────────────────────────────────────
    google_maps_api_key: str = Field(default="", alias="GOOGLE_MAPS_API_KEY")

    # ── Google Analytics / Tag Manager ────────────────────────────────────
    ga_measurement_id: str = Field(default="", alias="GA_MEASUREMENT_ID")
    gtm_container_id: str = Field(default="", alias="GTM_CONTAINER_ID")

    # ── Server ─────────────────────────────────────────────────────────────
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    @field_validator("gemini_api_key", "google_maps_api_key", mode="before")
    @classmethod
    def strip_quotes(cls, v: str) -> str:
        """Remove accidental quotes around API keys."""
        return str(v).strip().strip('"').strip("'")

    @property
    def cors_origins_list(self) -> List[str]:
        return self.cors_origins.split(",")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
