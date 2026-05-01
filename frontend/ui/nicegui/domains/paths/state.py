"""Typed state models for the Paths page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PathsPageState:
    """Typed UI state for the Paths page."""

    paths: list[dict[str, Any]] = field(default_factory=list)
    selected_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    selected_detail_by_path_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    tracking_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    courses: list[dict[str, Any]] = field(default_factory=list)
    course_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    learning_item_options: dict[str, str] = field(default_factory=dict)
    path_review_summary_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True)
class PathsPageUiState:
    """UI-only mutable state for pagination/loading controls."""

    page_size: int = 10
    visible_count: int = 10
    loading: bool = False
    loaded_once: bool = False


@dataclass(slots=True)
class PathDetailBundle:
    """Preloaded payloads for the path details dialog."""

    detail: dict[str, Any]
    path_reviews: list[dict[str, Any]]
    course_review_summary_by_course_id: dict[int, dict[str, Any]]
