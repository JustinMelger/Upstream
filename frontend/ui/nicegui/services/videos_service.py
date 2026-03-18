"""Video-service helpers for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


async def load_videos(
    *,
    api: ApiClient,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Load videos list payloads from the backend."""
    rows = await api.get("/videos", params=params or None)
    return [row for row in list(rows or []) if isinstance(row, dict)]
