"""Controller/orchestration for the Insights page."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


@dataclass(slots=True)
class HomeOverviewBundle:
    """Loaded payload used by insights dashboard."""

    snapshot_stats: dict[str, int]
    team_stats_by_user: list[dict[str, Any]]


class HomePageController:
    """Imperative API workflows for `/insights`."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.

        """
        self._api = api

    async def load_overview(
        self,
        *,
        username: str,
        is_admin: bool,
        mode_value: str,
    ) -> HomeOverviewBundle:
        """Load dashboard overview payload."""
        user = str(username or "")
        mode = str(mode_value or "mine")
        if is_admin and mode == "team":
            stats_payload, team_payload_raw = await asyncio.gather(
                self._api.get("/tracking/stats"),
                self._api.get("/tracking/stats/users"),
            )
            team_payload = list(team_payload_raw or [])
        else:
            stats_payload = await self._api.get("/tracking/stats", params={"colleague_id": user})
            team_payload = []

        return HomeOverviewBundle(
            snapshot_stats=dict(stats_payload or {}),
            team_stats_by_user=team_payload,
        )
