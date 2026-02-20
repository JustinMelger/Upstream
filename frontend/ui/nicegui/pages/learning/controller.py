"""Controller/orchestration for the Learning page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.learning_service import load_my_learning_data


class LearningPageController:
    """Imperative API workflows used by the Learning page."""

    def __init__(self, *, api: ApiClient):
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
        await self._api.post("/tracking", {"course_id": int(course_id), "status": str(status)})

    async def clear_tracking_status(self, *, course_id: int) -> None:
        """Clear tracking status for a course."""
        await self._api.post("/tracking/delete", {"course_id": int(course_id)})

    async def save_recommended_course(self, *, course_id: int) -> None:
        """Save a recommended course as interested."""
        await self._api.post("/tracking", {"course_id": int(course_id), "status": "interested"})

    async def save_recommended_path(self, *, path_id: int) -> None:
        """Save a recommended path as selected."""
        await self._api.post(f"/paths/{int(path_id)}/select", {})
