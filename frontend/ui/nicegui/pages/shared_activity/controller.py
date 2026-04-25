"""Controller orchestration for shared inbox/team feed loading."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.notifications_service import load_activity_feed


class ActivityPageController:
    """Imperative API workflows for shared inbox/team feeds."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.

        """
        self._api = api

    async def load_events(self, *, scope: str, limit: int = 50) -> list[dict[str, Any]]:
        """Load shared activity feed rows for the requested scope."""
        rows = await load_activity_feed(api=self._api, limit=int(limit), scope=str(scope or "inbox"))
        return [row for row in list(rows or []) if isinstance(row, dict)]
