from __future__ import annotations


"""Runtime configuration for the NiceGUI frontend."""

from dataclasses import dataclass, field
import os
from typing import Literal


SocketTransport = Literal["polling", "websocket"]


def _socket_transports_from_env() -> list[SocketTransport]:
    """Return Socket.IO browser transport order from env."""
    raw = os.getenv("NICEGUI_SOCKET_TRANSPORTS", "polling,websocket")
    values = [value.strip() for value in raw.split(",") if value.strip()]
    allowed: set[SocketTransport] = {"polling", "websocket"}
    transports: list[SocketTransport] = []
    for value in values:
        if value in allowed:
            transports.append(value)
    return transports or ["polling", "websocket"]


@dataclass(frozen=True, slots=True)
class UiSettings:
    """Runtime settings for the NiceGUI UI."""

    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    storage_secret: str = os.getenv("NICEGUI_STORAGE_SECRET", "dev-storage-secret-change-me")
    feature_ai_curator: bool = os.getenv("FEATURE_AI_CURATOR", "0") == "1"
    feature_articles: bool = os.getenv("FEATURE_ARTICLES", "1") == "1"
    feature_telemetry: bool = os.getenv("FEATURE_TELEMETRY", "0") == "1"
    reload: bool = os.getenv("NICEGUI_RELOAD", "0") == "1"
    host: str = os.getenv("NICEGUI_HOST", "0.0.0.0")
    port: int = int(os.getenv("NICEGUI_PORT", "8080"))
    show: bool = os.getenv("NICEGUI_SHOW", "0") == "1"
    reconnect_timeout_s: float = float(os.getenv("NICEGUI_RECONNECT_TIMEOUT", "30"))
    socket_transports: list[SocketTransport] = field(default_factory=_socket_transports_from_env)
    websocket_max_bytes: int = int(os.getenv("NICEGUI_WEBSOCKET_MAX_BYTES", "10000000"))
    message_history_length: int = int(os.getenv("NICEGUI_MESSAGE_HISTORY_LENGTH", "0"))


settings = UiSettings()
