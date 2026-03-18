"""Pure helpers for learning-item subtype normalization and display."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


_SUPPORTED_ITEM_TYPES = {"video", "course", "article"}
_TYPE_LABELS = {
    "video": "Video",
    "course": "Course",
    "article": "Article",
}
_PRIMARY_ACTION_LABELS = {
    "video": "Watch video",
    "course": "Open course",
    "article": "Read article",
}
_SOURCE_ACTION_LABELS = {
    "video": "Open video source",
    "course": "Open course source",
    "article": "Open article source",
}
_REVIEW_ACTION_LABELS = {
    "course": "Review course",
    "article": "Review article",
}
_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
}
_COURSE_HOSTS = {
    "udemy.com",
    "www.udemy.com",
}
_DISPLAY_ORDER = ("video", "course", "article")


@dataclass(frozen=True, slots=True)
class LearningItemCapabilities:
    """Capabilities intentionally supported by one learning-item subtype."""

    item_type: str
    supports_tracking: bool
    supports_reviews: bool
    supports_recommendations: bool


_TYPE_CAPABILITIES = {
    "video": LearningItemCapabilities(
        item_type="video",
        supports_tracking=False,
        supports_reviews=False,
        supports_recommendations=False,
    ),
    "course": LearningItemCapabilities(
        item_type="course",
        supports_tracking=True,
        supports_reviews=True,
        supports_recommendations=True,
    ),
    "article": LearningItemCapabilities(
        item_type="article",
        supports_tracking=False,
        supports_reviews=True,
        supports_recommendations=False,
    ),
}


def normalize_learning_item_type(value: str, *, default: str = "course") -> str:
    """Normalize a learning-item subtype to a supported value."""
    cleaned = str(value or "").strip().lower()
    if cleaned in _SUPPORTED_ITEM_TYPES:
        return cleaned
    return str(default or "course").strip().lower() if str(default or "").strip().lower() in _SUPPORTED_ITEM_TYPES else "course"


def infer_learning_item_type(*, url: str = "", provider: str = "", fallback: str = "article") -> str:
    """Infer learning-item subtype from URL/provider hints."""
    normalized_fallback = normalize_learning_item_type(fallback, default="article")
    host = str(urlparse(str(url or "").strip()).hostname or "").strip().lower()
    provider_value = str(provider or "").strip().lower()

    if host in _VIDEO_HOSTS or "youtube" in provider_value or "vimeo" in provider_value:
        return "video"
    if host in _COURSE_HOSTS or "udemy" in provider_value:
        return "course"
    return normalized_fallback


def learning_item_type_label(item_type: str) -> str:
    """Return the compact UI label for a learning-item subtype."""
    normalized = normalize_learning_item_type(item_type, default="course")
    return str(_TYPE_LABELS.get(normalized) or "Learning Item")


def learning_item_capabilities(item_type: str) -> LearningItemCapabilities:
    """Return intentional feature support for one learning-item subtype."""
    normalized = normalize_learning_item_type(item_type, default="course")
    return _TYPE_CAPABILITIES.get(normalized, _TYPE_CAPABILITIES["course"])


def learning_item_primary_action_label(item_type: str) -> str:
    """Return the primary CTA label for one learning-item subtype."""
    normalized = normalize_learning_item_type(item_type, default="course")
    return str(_PRIMARY_ACTION_LABELS.get(normalized) or "Open details")


def learning_item_review_action_label(item_type: str) -> str:
    """Return the review CTA label for one learning-item subtype."""
    normalized = normalize_learning_item_type(item_type, default="course")
    return str(_REVIEW_ACTION_LABELS.get(normalized) or "Review")


def learning_item_source_action_label(item_type: str) -> str:
    """Return the source-link CTA label for one learning-item subtype."""
    normalized = normalize_learning_item_type(item_type, default="course")
    return str(_SOURCE_ACTION_LABELS.get(normalized) or "Open source")


def interleave_learning_item_entries(*, entries: list[Any]) -> list[Any]:
    """Interleave learning items by subtype to preserve visible diversity."""
    buckets: dict[str, deque[Any]] = {item_type: deque() for item_type in _DISPLAY_ORDER}
    trailing: list[Any] = []

    for entry in list(entries or []):
        raw_type = entry.get("learning_item_type") if isinstance(entry, dict) else getattr(entry, "learning_item_type", "")
        item_type = normalize_learning_item_type(str(raw_type or ""), default="")
        if item_type in buckets:
            buckets[item_type].append(entry)
        else:
            trailing.append(entry)

    ordered: list[Any] = []
    while any(buckets[item_type] for item_type in _DISPLAY_ORDER):
        for item_type in _DISPLAY_ORDER:
            if buckets[item_type]:
                ordered.append(buckets[item_type].popleft())
    ordered.extend(trailing)
    return ordered
