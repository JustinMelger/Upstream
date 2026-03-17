"""Controller/orchestration for video-domain workflows."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.videos_service import load_videos


class VideosPageController:
    """Imperative API workflows for videos."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller."""
        self._api = api

    async def load_list(self, *, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Load videos list payload."""
        return list(await load_videos(api=self._api, params=params))

    async def create_video(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new video row."""
        return dict(await self._api.post("/videos", dict(payload or {})) or {})

    async def suggest_video_from_url(self, *, url: str) -> dict[str, Any]:
        """Resolve URL metadata suggestions for the share dialog."""
        return dict(await self._api.post("/url-preview/metadata", {"url": str(url or "").strip()}) or {})

    async def load_video(self, *, video_id: int) -> dict[str, Any]:
        """Load one video detail payload."""
        return dict(await self._api.get(f"/videos/{int(video_id)}") or {})
