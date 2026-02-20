"""Controller/orchestration layer for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.courses_service import (
    load_courses_and_tracking,
    load_recommendation_summaries,
    load_review_summaries,
    load_tracking_map,
)


@dataclass(slots=True)
class CoursesListBundle:
    """Preloaded payloads used by the courses list view."""

    courses: list[dict[str, Any]]
    tracking_by_course_id: dict[int, dict[str, Any]]
    review_summary_by_course_id: dict[int, dict[str, Any]]
    recommendation_summary_by_course_id: dict[int, dict[str, Any]]


class CoursesPageController:
    """Imperative API workflow orchestration for Courses page."""

    def __init__(self, *, api: ApiClient):
        self._api = api

    async def load_list_bundle(self, *, params: dict[str, Any] | None = None) -> CoursesListBundle:
        """Load list-view courses and social summaries for current filters."""
        courses, tracking_by_course_id = await load_courses_and_tracking(api=self._api, course_params=params or None)
        course_ids = [int(c.get("id") or 0) for c in courses if int(c.get("id") or 0) > 0]
        review_summary_by_course_id = await load_review_summaries(api=self._api, course_ids=course_ids)
        recommendation_summary_by_course_id = await load_recommendation_summaries(api=self._api, course_ids=course_ids)
        return CoursesListBundle(
            courses=courses,
            tracking_by_course_id=tracking_by_course_id,
            review_summary_by_course_id=review_summary_by_course_id,
            recommendation_summary_by_course_id=recommendation_summary_by_course_id,
        )

    async def reload_tracking(self) -> dict[int, dict[str, Any]]:
        """Load current user's tracking map only."""
        return await load_tracking_map(api=self._api)

    async def load_recommendation_summary_for_course(self, *, course_id: int) -> dict[str, Any] | None:
        """Load recommendation summary row for a single course id."""
        rows = await load_recommendation_summaries(api=self._api, course_ids=[int(course_id)])
        row = rows.get(int(course_id))
        return dict(row) if isinstance(row, dict) else None
