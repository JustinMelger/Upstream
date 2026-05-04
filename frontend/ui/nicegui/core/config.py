from __future__ import annotations


"""Runtime configuration for the NiceGUI frontend."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class UiSettings:
    """Runtime settings for the NiceGUI UI."""

    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    storage_secret: str = os.getenv("NICEGUI_STORAGE_SECRET", "dev-storage-secret-change-me")
    feature_ai_curator: bool = os.getenv("FEATURE_AI_CURATOR", "0") == "1"
    feature_articles: bool = os.getenv("FEATURE_ARTICLES", "1") == "1"
    feature_telemetry: bool = os.getenv("FEATURE_TELEMETRY", "0") == "1"
    reload: bool = os.getenv("NICEGUI_RELOAD", "0") == "1"
    websocket_max_bytes: int = int(os.getenv("NICEGUI_WEBSOCKET_MAX_BYTES", "10000000"))
    message_history_length: int = int(os.getenv("NICEGUI_MESSAGE_HISTORY_LENGTH", "0"))


settings = UiSettings()
