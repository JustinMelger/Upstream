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
