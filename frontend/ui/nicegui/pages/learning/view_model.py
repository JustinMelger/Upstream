"""Typed view-model helpers for the Learning page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SharedTabView:
    """Projection of shared-tab data consumed by UI renderers."""

    shared_courses: list[dict[str, Any]]
    shared_paths: list[dict[str, Any]]
    shared_articles: list[dict[str, Any]]
    shared_course_review_summary_by_id: dict[int, dict[str, Any]]
    shared_course_recommendation_summary_by_id: dict[int, dict[str, Any]]
    shared_path_review_summary_by_id: dict[int, dict[str, Any]]
    shared_path_recommendation_summary_by_id: dict[int, dict[str, Any]]


@dataclass(slots=True)
class LearningTabView:
    """Projection of learning-tab data consumed by UI renderers."""

    tracked_courses: list[dict[str, Any]]
    tracking_by_course_id: dict[int, dict[str, Any]]
    selected_paths: list[dict[str, Any]]
    path_details_by_id: dict[int, dict[str, Any]]
    course_review_summary_by_id: dict[int, dict[str, Any]]
    path_review_summary_by_id: dict[int, dict[str, Any]]
    pending_course_review_ids: list[int]
    pending_path_review_ids: list[int]
    recommended_courses: list[dict[str, Any]]
    recommended_paths: list[dict[str, Any]]


def build_shared_tab_view(*, data: dict[str, Any]) -> SharedTabView:
    """Build typed shared-tab projection from raw page data payload."""
    return SharedTabView(
        shared_courses=list(data.get("shared_courses") or []),
        shared_paths=list(data.get("shared_paths") or []),
        shared_articles=list(data.get("shared_articles") or []),
        shared_course_review_summary_by_id=dict(data.get("shared_course_review_summary_by_id") or {}),
        shared_course_recommendation_summary_by_id=dict(data.get("shared_course_recommendation_summary_by_id") or {}),
        shared_path_review_summary_by_id=dict(data.get("shared_path_review_summary_by_id") or {}),
        shared_path_recommendation_summary_by_id=dict(data.get("shared_path_recommendation_summary_by_id") or {}),
    )


def build_learning_tab_view(
    *,
    data: dict[str, Any],
    dismissed_recommended_course_ids: set[int],
    dismissed_recommended_path_ids: set[int],
) -> LearningTabView:
    """Build typed learning-tab projection from raw page data payload."""
    pending_course_review_ids = sorted({int(i) for i in list(data.get("pending_course_review_ids") or [])})
    pending_path_review_ids = sorted({int(i) for i in list(data.get("pending_path_review_ids") or [])})

    def _valid_int_id(value: Any) -> int | None:
        try:
            parsed = int(value or 0)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    recommended_courses = [
        r
        for r in list(data.get("recommended_courses_for_you") or [])
        if isinstance(r, dict)
        and (course_id := _valid_int_id(r.get("course_id"))) is not None
        and course_id not in dismissed_recommended_course_ids
    ]
    recommended_paths = [
        r
        for r in list(data.get("recommended_paths_for_you") or [])
        if isinstance(r, dict)
        and (path_id := _valid_int_id(r.get("path_id"))) is not None
        and path_id not in dismissed_recommended_path_ids
    ]
    return LearningTabView(
        tracked_courses=list(data.get("tracked_courses") or []),
        tracking_by_course_id=dict(data.get("tracking_by_course_id") or {}),
        selected_paths=list(data.get("selected_paths") or []),
        path_details_by_id=dict(data.get("path_details_by_id") or {}),
        course_review_summary_by_id=dict(data.get("course_review_summary_by_id") or {}),
        path_review_summary_by_id=dict(data.get("path_review_summary_by_id") or {}),
        pending_course_review_ids=pending_course_review_ids,
        pending_path_review_ids=pending_path_review_ids,
        recommended_courses=recommended_courses,
        recommended_paths=recommended_paths,
    )
