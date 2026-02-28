"""Controller workflows for the Teams page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.notifications_service import load_activity_feed
from frontend.ui.nicegui.services.teams_service import (
    add_team_member,
    create_team,
    get_team_detail,
    list_my_teams,
    list_team_activity,
    remove_team_member,
)


class TeamsPageController:
    """Imperative API workflows for `/teams`."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.
        """
        self._api = api

    async def list_my_teams(self) -> list[dict[str, Any]]:
        """Load teams the current user belongs to."""
        return await list_my_teams(api=self._api)

    async def create_team(self, *, name: str, description: str | None) -> dict[str, Any]:
        """Create team and return detail payload."""
        return await create_team(api=self._api, name=name, description=description)

    async def get_team_detail(self, *, team_id: int) -> dict[str, Any]:
        """Load one team detail."""
        return await get_team_detail(api=self._api, team_id=int(team_id))

    async def add_member(self, *, team_id: int, user_id: str, role: str) -> dict[str, Any]:
        """Add/update one team member."""
        return await add_team_member(api=self._api, team_id=int(team_id), user_id=user_id, role=role)

    async def remove_member(self, *, team_id: int, user_id: str) -> int:
        """Remove one team member."""
        return await remove_team_member(api=self._api, team_id=int(team_id), user_id=user_id)

    async def list_activity(self, *, team_id: int, limit: int = 30) -> list[dict[str, Any]]:
        """Load team-scoped activity rows."""
        return await list_team_activity(api=self._api, team_id=int(team_id), limit=int(limit))

    async def list_inbox(self, *, limit: int = 40) -> list[dict[str, Any]]:
        """Load personal inbox activity rows."""
        return await load_activity_feed(api=self._api, limit=int(limit), scope="inbox")
