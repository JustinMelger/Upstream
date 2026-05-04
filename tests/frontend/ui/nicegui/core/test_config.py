from __future__ import annotations

import importlib

from frontend.ui.nicegui.core import config


def test_ui_config_defaults_for_container_runtime(monkeypatch):
    monkeypatch.delenv("NICEGUI_HOST", raising=False)
    monkeypatch.delenv("NICEGUI_PORT", raising=False)
    monkeypatch.delenv("NICEGUI_SHOW", raising=False)
    monkeypatch.delenv("NICEGUI_RECONNECT_TIMEOUT", raising=False)
    monkeypatch.delenv("NICEGUI_SOCKET_TRANSPORTS", raising=False)

    importlib.reload(config)

    assert config.settings.host == "0.0.0.0"
    assert config.settings.port == 8080
    assert config.settings.show is False
    assert config.settings.reconnect_timeout_s == 30
    assert config.settings.socket_transports == ["polling", "websocket"]


def test_ui_config_env_overrides(monkeypatch):
    monkeypatch.setenv("NICEGUI_HOST", "127.0.0.1")
    monkeypatch.setenv("NICEGUI_PORT", "9090")
    monkeypatch.setenv("NICEGUI_SHOW", "1")
    monkeypatch.setenv("NICEGUI_RECONNECT_TIMEOUT", "45.5")
    monkeypatch.setenv("NICEGUI_SOCKET_TRANSPORTS", "websocket,polling")

    importlib.reload(config)

    assert config.settings.host == "127.0.0.1"
    assert config.settings.port == 9090
    assert config.settings.show is True
    assert config.settings.reconnect_timeout_s == 45.5
    assert config.settings.socket_transports == ["websocket", "polling"]


def test_ui_config_ignores_invalid_socket_transports(monkeypatch):
    monkeypatch.setenv("NICEGUI_SOCKET_TRANSPORTS", "bad,polling")

    importlib.reload(config)

    assert config.settings.socket_transports == ["polling"]
