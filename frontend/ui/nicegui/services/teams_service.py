"""Use-cases for teams and team-scoped activity."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from frontend.ui.nicegui.core.api_client import ApiClient


async def list_my_teams(*, api: ApiClient) -> list[dict[str, Any]]:
    """Load teams where the current user is a member."""
    rows = await api.get("/teams/mine")
    return [row for row in list(rows or []) if isinstance(row, dict)]


async def create_team(*, api: ApiClient, name: str, description: str | None) -> dict[str, Any]:
    """Create a team and return team detail payload."""
    payload = {
        "name": str(name or "").strip(),
        "description": str(description or "").strip(),
    }
    row = await api.post("/teams", payload)
    return dict(row or {})


async def get_team_detail(*, api: ApiClient, team_id: int) -> dict[str, Any]:
    """Load full team detail by id."""
    row = await api.get(f"/teams/{int(team_id)}")
    return dict(row or {})


async def add_team_member(*, api: ApiClient, team_id: int, user_id: str, role: str) -> dict[str, Any]:
    """Add/update a team member."""
    payload = {
        "user_id": str(user_id or "").strip(),
        "role": str(role or "member").strip().lower(),
    }
    row = await api.post(f"/teams/{int(team_id)}/members", payload)
    return dict(row or {})


async def remove_team_member(*, api: ApiClient, team_id: int, user_id: str) -> int:
    """Remove a team member and return removed row count."""
    encoded_user = quote(str(user_id or "").strip(), safe="")
    row = await api.delete(f"/teams/{int(team_id)}/members/{encoded_user}")
    if not isinstance(row, dict):
        return 0
    return int(row.get("removed") or 0)


async def list_team_activity(*, api: ApiClient, team_id: int, limit: int = 30) -> list[dict[str, Any]]:
    """Load team-scoped activity feed rows."""
    rows = await api.get(f"/teams/{int(team_id)}/activity", params={"limit": max(1, min(int(limit), 100))})
    return [row for row in list(rows or []) if isinstance(row, dict)]
