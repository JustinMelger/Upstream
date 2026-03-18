"""Typed state models for the Explore page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExplorePageState:
    """Mutable state for Explore list data and UI flags."""

    loading: bool = False
    loaded_once: bool = False
    articles_loading: bool = False
    videos_loading: bool = False
    paths_loading: bool = False
    courses: list[dict[str, Any]] = field(default_factory=list)
    videos: list[dict[str, Any]] = field(default_factory=list)
    video_review_summary_by_video_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    tracking_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    course_review_summary_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    course_recommendation_summary_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    paths: list[dict[str, Any]] = field(default_factory=list)
    selected_by_path_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    selected_detail_by_path_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    path_review_summary_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    path_recommendation_summary_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    articles: list[dict[str, Any]] = field(default_factory=list)
    article_review_summary_by_article_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    preview_course_id: int | None = None


@dataclass(slots=True)
class ExploreUiFlags:
    """Mutable UI-only flags for Explore page event behavior."""

    search_telemetry_emitted: bool = False
    show_all_categories: bool = True
    learning_items_visible_limit: int = 8
