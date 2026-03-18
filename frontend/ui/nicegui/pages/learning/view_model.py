"""Typed view-model helpers for the Learning page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.learning_items import (
    infer_learning_item_type,
    learning_item_capabilities,
    LearningItemCapabilities,
)


@dataclass(slots=True)
class SharedLearningItemView:
    """Typed shared learning-item card projection for non-Explore surfaces."""

    item_type: str
    item_id: int
    title: str
    capabilities: LearningItemCapabilities
    review_summary_row: dict[str, Any] | None
    recommendation_summary_row: dict[str, Any] | None


@dataclass(slots=True)
class SharedTabView:
    """Projection of shared-tab data consumed by UI renderers."""

    shared_learning_items: list[SharedLearningItemView]
    shared_courses: list[dict[str, Any]]
    shared_videos: list[dict[str, Any]]
    shared_paths: list[dict[str, Any]]
    shared_articles: list[dict[str, Any]]
    shared_course_review_summary_by_id: dict[int, dict[str, Any]]
    shared_course_recommendation_summary_by_id: dict[int, dict[str, Any]]
    shared_video_review_summary_by_id: dict[int, dict[str, Any]]
    shared_path_review_summary_by_id: dict[int, dict[str, Any]]
    shared_path_recommendation_summary_by_id: dict[int, dict[str, Any]]


def _shared_learning_item_sort_key(item: SharedLearningItemView) -> tuple[str, int, str]:
    return (item.item_type, int(item.item_id), str(item.title or "").lower())


def build_shared_learning_item_views(
    *,
    shared_courses: list[dict[str, Any]],
    shared_videos: list[dict[str, Any]],
    shared_articles: list[dict[str, Any]],
    course_review_summary_by_id: dict[int, dict[str, Any]],
    course_recommendation_summary_by_id: dict[int, dict[str, Any]],
    video_review_summary_by_id: dict[int, dict[str, Any]],
) -> list[SharedLearningItemView]:
    """Build typed shared learning-item rows from shared courses/articles."""
    items: list[SharedLearningItemView] = []
    for row in list(shared_courses or []):
        item_id = int(row.get("id") or 0)
        if item_id <= 0:
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        item_type = infer_learning_item_type(
            url=str(row.get("url") or ""),
            provider=str(row.get("provider") or ""),
            fallback="course",
        )
        items.append(
            SharedLearningItemView(
                item_type=item_type,
                item_id=item_id,
                title=title,
                capabilities=learning_item_capabilities(item_type),
                review_summary_row=dict(course_review_summary_by_id.get(item_id) or {}) or None,
                recommendation_summary_row=dict(course_recommendation_summary_by_id.get(item_id) or {}) or None,
            )
        )
    for row in list(shared_articles or []):
        item_id = int(row.get("id") or 0)
        if item_id <= 0:
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        items.append(
            SharedLearningItemView(
                item_type="article",
                item_id=item_id,
                title=title,
                capabilities=learning_item_capabilities("article"),
                review_summary_row=None,
                recommendation_summary_row=None,
            )
        )
    for row in list(shared_videos or []):
        item_id = int(row.get("id") or 0)
        if item_id <= 0:
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        items.append(
            SharedLearningItemView(
                item_type="video",
                item_id=item_id,
                title=title,
                capabilities=learning_item_capabilities("video"),
                review_summary_row=dict(video_review_summary_by_id.get(item_id) or {}) or None,
                recommendation_summary_row=None,
            )
        )
    return sorted(items, key=_shared_learning_item_sort_key)


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


def build_recently_shared_in_teams(
    *,
    data: dict[str, Any],
    username: str,
    limit: int = 6,
) -> list[dict[str, Any]]:
    """Return a recency-sorted mixed feed of teammate-shared content."""

    def _append_rows(content_type: str, rows: list[dict[str, Any]], title_key: str) -> None:
        for row in rows:
            owner = str(row.get("created_by") or "").strip()
            if not owner or owner == username:
                continue
            try:
                item_id = int(row.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if item_id <= 0:
                continue
            title = str(row.get(title_key) or "").strip()
            if not title:
                continue
            updated_at = str(row.get("updated_at") or row.get("created_at") or "").strip()
            feed.append(
                {
                    "type": content_type,
                    "id": item_id,
                    "title": title,
                    "created_by": owner,
                    "updated_at": updated_at,
                }
            )

    feed: list[dict[str, Any]] = []
    _append_rows("course", list(data.get("courses") or []), "title")
    _append_rows("video", list(data.get("videos") or []), "title")
    _append_rows("path", list(data.get("paths") or []), "name")
    _append_rows("article", list(data.get("articles") or []), "title")
    feed.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    return feed[: max(0, int(limit))]


def build_shared_tab_view(*, data: dict[str, Any]) -> SharedTabView:
    """Build typed shared-tab projection from raw page data payload."""
    shared_courses = list(data.get("shared_courses") or [])
    shared_videos = list(data.get("shared_videos") or [])
    shared_articles = list(data.get("shared_articles") or [])
    shared_course_review_summary_by_id = dict(data.get("shared_course_review_summary_by_id") or {})
    shared_course_recommendation_summary_by_id = dict(data.get("shared_course_recommendation_summary_by_id") or {})
    shared_video_review_summary_by_id = dict(data.get("shared_video_review_summary_by_id") or {})
    return SharedTabView(
        shared_learning_items=build_shared_learning_item_views(
            shared_courses=shared_courses,
            shared_videos=shared_videos,
            shared_articles=shared_articles,
            course_review_summary_by_id=shared_course_review_summary_by_id,
            course_recommendation_summary_by_id=shared_course_recommendation_summary_by_id,
            video_review_summary_by_id=shared_video_review_summary_by_id,
        ),
        shared_courses=shared_courses,
        shared_videos=shared_videos,
        shared_paths=list(data.get("shared_paths") or []),
        shared_articles=shared_articles,
        shared_course_review_summary_by_id=shared_course_review_summary_by_id,
        shared_course_recommendation_summary_by_id=shared_course_recommendation_summary_by_id,
        shared_video_review_summary_by_id=shared_video_review_summary_by_id,
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

    def _valid_int_id(value: Any) -> int | None:
        try:
            parsed = int(value or 0)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def _sorted_positive_ids(values: list[Any]) -> list[int]:
        ids: set[int] = set()
        for raw in values:
            parsed = _valid_int_id(raw)
            if parsed is not None:
                ids.add(parsed)
        return sorted(ids)

    pending_course_review_ids = _sorted_positive_ids(list(data.get("pending_course_review_ids") or []))
    pending_path_review_ids = _sorted_positive_ids(list(data.get("pending_path_review_ids") or []))

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
