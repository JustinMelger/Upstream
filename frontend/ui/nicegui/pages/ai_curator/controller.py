"""Controller orchestration for the AI Curator page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.ai_curator_service import (
    apply_plan,
    generate_plan,
)


class AiCuratorPageController:
    """Imperative API workflows for `/ai`."""

    def __init__(self, *, api: ApiClient):
        self._api = api

    async def generate_plan(self, *, goal: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Generate draft path/courses from goal."""
        return await generate_plan(api=self._api, goal=goal)

    async def apply_plan(
        self,
        *,
        draft_courses: list[dict[str, Any]],
        path_name: str,
        path_description: str,
        select_for_me: bool,
    ) -> int:
        """Create courses/path from editable draft and optionally select path."""
        return await apply_plan(
            api=self._api,
            draft_courses=draft_courses,
            path_name=path_name,
            path_description=path_description,
            select_for_me=select_for_me,
        )
