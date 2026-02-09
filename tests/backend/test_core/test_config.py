import importlib

import pytest

import backend.core.config as config


@pytest.mark.unit
def test_config_defaults(monkeypatch):
    """Settings use defaults when environment variables are missing."""
    monkeypatch.delenv("API_TITLE", raising=False)
    monkeypatch.delenv("API_VERSION", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SESSION_DAYS", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)

    importlib.reload(config)

    assert config.settings.api_title == "Learning Hub API"
    assert config.settings.api_version == "0.1.0"
    assert config.settings.database_url == ""
    assert config.settings.session_days == 30
    assert config.settings.bootstrap_admin_username == "admin"
    assert config.settings.bootstrap_admin_password == "admin"


@pytest.mark.unit
def test_config_env_overrides(monkeypatch):
    """Settings read environment overrides on import."""
    monkeypatch.setenv("API_TITLE", "Custom API")
    monkeypatch.setenv("API_VERSION", "9.9.9")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    monkeypatch.setenv("SESSION_DAYS", "7")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_USERNAME", "root")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "secret")

    importlib.reload(config)

    assert config.settings.api_title == "Custom API"
    assert config.settings.api_version == "9.9.9"
    assert config.settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert config.settings.session_days == 7
    assert config.settings.bootstrap_admin_username == "root"
    assert config.settings.bootstrap_admin_password == "secret"
