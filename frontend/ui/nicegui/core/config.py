from __future__ import annotations


"""Runtime configuration for the NiceGUI frontend."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class UiSettings:
    """Runtime settings for the NiceGUI UI."""

    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    storage_secret: str = os.getenv("NICEGUI_STORAGE_SECRET", "dev-storage-secret-change-me")
    feature_ai_curator: bool = os.getenv("FEATURE_AI_CURATOR", "1") == "1"
    feature_articles: bool = os.getenv("FEATURE_ARTICLES", "1") == "1"
    feature_explore_cinema: bool = os.getenv("FEATURE_EXPLORE_CINEMA", "1") == "1"


settings = UiSettings()
