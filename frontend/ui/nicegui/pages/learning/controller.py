"""Controller/orchestration for the Learning page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.learning_service import (
    clear_tracking_status,
    load_my_learning_data,
    save_recommended_course,
    save_recommended_path,
    set_tracking_status,
)


class LearningPageController:
    """Imperative API workflows used by the Learning page."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.

        """
        self._api = api

    async def load_page_data(self, *, username: str, include_articles: bool) -> dict[str, Any]:
        """Load all data required by the learning view."""
        return await load_my_learning_data(
            api=self._api,
            username=str(username or ""),
            include_articles=bool(include_articles),
        )

    async def set_tracking_status(self, *, course_id: int, status: str) -> None:
        """Set tracking status for a course."""
        await set_tracking_status(api=self._api, course_id=int(course_id), status=str(status))

    async def clear_tracking_status(self, *, course_id: int) -> None:
        """Clear tracking status for a course."""
        await clear_tracking_status(api=self._api, course_id=int(course_id))

    async def save_recommended_course(self, *, course_id: int) -> None:
        """Track a recommended course as interested."""
        await save_recommended_course(api=self._api, course_id=int(course_id))

    async def save_recommended_path(self, *, path_id: int) -> None:
        """Select a recommended path."""
        await save_recommended_path(api=self._api, path_id=int(path_id))
