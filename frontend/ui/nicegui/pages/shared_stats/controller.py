"""Controller/orchestration for shared Home/Profile stats loading."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


@dataclass(slots=True)
class SharedStatsOverviewBundle:
    """Loaded payload used by shared Home/Profile stats surfaces."""

    snapshot_stats: dict[str, int]
    team_stats_by_user: list[dict[str, Any]]


class SharedStatsController:
    """Imperative API workflows for shared Home/Profile stats surfaces."""

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
    ) -> SharedStatsOverviewBundle:
        """Load dashboard overview payload."""
        user = str(username or "")
        mode = str(mode_value or "mine")
        if mode == "team":
            stats_payload, team_payload_raw = await asyncio.gather(
                self._api.get("/tracking/stats"),
                self._api.get("/tracking/stats/users"),
            )
            team_payload = list(team_payload_raw or [])
        else:
            _ = is_admin
            stats_payload = await self._api.get("/tracking/stats", params={"colleague_id": user})
            team_payload = []

        return SharedStatsOverviewBundle(
            snapshot_stats=dict(stats_payload or {}),
            team_stats_by_user=team_payload,
        )
