"""Controller/orchestration layer for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.courses_service import (
    clear_course_detail_cache,
    CourseDetailBundle,
    load_course_detail_bundle,
    load_courses_and_tracking,
    load_review_summaries,
    load_tracking_map,
)


@dataclass(slots=True)
class CoursesListBundle:
    """Preloaded payloads used by the courses list view."""

    courses: list[dict[str, Any]]
    tracking_by_course_id: dict[int, dict[str, Any]]
    review_summary_by_course_id: dict[int, dict[str, Any]]


class CoursesPageController:
    """Imperative API workflow orchestration for Courses page."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.

        """
        self._api = api

    async def load_list_bundle(self, *, params: dict[str, Any] | None = None) -> CoursesListBundle:
        """Load list-view courses and social summaries for current filters."""
        courses, tracking_by_course_id = await load_courses_and_tracking(api=self._api, course_params=params or None)
        course_ids = [int(c.get("id") or 0) for c in courses if int(c.get("id") or 0) > 0]
        review_summary_by_course_id = await load_review_summaries(api=self._api, course_ids=course_ids)
        return CoursesListBundle(
            courses=courses,
            tracking_by_course_id=tracking_by_course_id,
            review_summary_by_course_id=review_summary_by_course_id,
        )

    async def reload_tracking(self) -> dict[int, dict[str, Any]]:
        """Load current user's tracking map only."""
        return await load_tracking_map(api=self._api)

    async def set_tracking_status(self, *, course_id: int, status: str) -> None:
        """Persist a tracking status for one course."""
        await self._api.post("/tracking", {"course_id": int(course_id), "status": str(status)})

    async def clear_tracking_status(self, *, course_id: int) -> None:
        """Remove tracking status for one course."""
        await self._api.post("/tracking/delete", {"course_id": int(course_id)})

    async def create_course(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a course."""
        return dict(await self._api.post("/courses", dict(payload or {})) or {})

    async def suggest_course_from_url(self, *, url: str) -> dict[str, Any]:
        """Resolve URL metadata suggestions for the share dialog."""
        payload = {"url": str(url or "").strip()}
        return dict(await self._api.post("/url-preview/metadata", payload) or {})

    async def update_course(self, *, course_id: int, payload: dict[str, Any]) -> None:
        """Update a course."""
        await self._api.put(f"/courses/{int(course_id)}", dict(payload or {}))

    async def delete_course(self, *, course_id: int) -> None:
        """Delete a course."""
        await self._api.delete(f"/courses/{int(course_id)}")

    async def load_course_detail_bundle(self, *, course_id: int, cache_scope: str) -> CourseDetailBundle:
        """Load detail payload (course, reviews) with short-lived cache."""
        return await load_course_detail_bundle(api=self._api, course_id=int(course_id), cache_scope=str(cache_scope or ""))

    async def save_course_review(self, *, course_id: int, rating: int, text: str, cache_scope: str) -> dict[str, Any]:
        """Create/update current user's review and invalidate detail cache."""
        out = await self._api.post(
            f"/courses/{int(course_id)}/reviews",
            {"rating": int(rating), "text": str(text or "")},
        )
        clear_course_detail_cache(course_id=int(course_id), cache_scope=str(cache_scope or ""))
        return dict(out or {})

    async def delete_course_review(self, *, course_id: int, review_id: int, cache_scope: str) -> bool:
        """Delete a review and invalidate detail cache."""
        await self._api.delete(f"/courses/{int(course_id)}/reviews/{int(review_id)}")
        clear_course_detail_cache(course_id=int(course_id), cache_scope=str(cache_scope or ""))
        return True

    def clear_course_detail_cache(self, *, course_id: int, cache_scope: str = "") -> None:
        """Invalidate cached course-detail payloads for one course/user scope."""
        clear_course_detail_cache(course_id=int(course_id), cache_scope=str(cache_scope or ""))
