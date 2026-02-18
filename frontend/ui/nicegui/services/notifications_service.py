"""Use-cases for notifications/activity feed."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


async def load_activity_feed(*, api: ApiClient, limit: int = 40, scope: str = "inbox") -> list[dict[str, Any]]:
    """Load recent activity feed rows and normalize to dicts."""
    scope_value = str(scope or "inbox").strip().lower()
    if scope_value not in {"inbox", "team"}:
        scope_value = "inbox"
    rows = await api.get(
        "/notifications/activity",
        params={"limit": max(1, min(int(limit), 100)), "scope": scope_value},
    )
    return [row for row in list(rows or []) if isinstance(row, dict)]
