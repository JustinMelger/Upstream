from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    api_title: str = "Learning Hub API"
    api_version: str = "0.1.0"
    api_root_path: str = ""
    database_url: str = ""
    session_days: int = 30
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin"
    environment: str = "development"
    browser_secret: str = "local-browser-secret-change-before-production"
    public_origin: str = "http://localhost:8080"

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        """Reject insecure production authentication configuration."""
        if self.environment == "production":
            if len(self.browser_secret) < 32 or self.browser_secret.startswith("local-"):
                raise ValueError("Production requires an explicit BROWSER_SECRET of at least 32 characters")
            if self.bootstrap_admin_password in {"", "admin", "change-me"}:
                raise ValueError("Production requires an explicit BOOTSTRAP_ADMIN_PASSWORD")
            if not self.public_origin.startswith("https://"):
                raise ValueError("Production requires an HTTPS PUBLIC_ORIGIN")
        return self

    feature_telemetry: bool = False
    otel_enabled: bool = False
    otel_service_name: str = "learning-hub-api"
    otel_service_version: str = "0.1.0"
    otel_deployment_environment: str = "dev"
    otel_traces_sample_ratio: float = 1.0
    otel_metrics_export_interval_ms: int = 60000
    otel_exporter_otlp_traces_endpoint: str = "http://localhost:4318/v1/traces"
    otel_exporter_otlp_metrics_endpoint: str = "http://localhost:4318/v1/metrics"
    otel_exporter_otlp_headers: str = ""


settings = Settings()
