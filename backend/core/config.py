from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    api_title: str = "Learning Hub API"
    api_version: str = "0.1.0"
    database_url: str = ""
    session_days: int = 30
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin"


settings = Settings()
