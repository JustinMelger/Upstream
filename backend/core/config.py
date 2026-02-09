from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    api_title: str = os.getenv("API_TITLE", "Learning Hub API")
    api_version: str = os.getenv("API_VERSION", "0.1.0")
    database_url: str = os.getenv("DATABASE_URL", "")
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))
    bootstrap_admin_username: str = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin")


settings = Settings()
