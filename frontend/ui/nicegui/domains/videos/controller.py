"""Controller/orchestration for video-domain workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.videos_service import load_videos


@dataclass(slots=True)
class VideosListBundle:
    """Loaded list payload for video surfaces."""

    videos: list[dict[str, Any]]
    review_summary_by_video_id: dict[int, dict[str, Any]]


class VideosPageController:
    """Imperative API workflows for videos."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller."""
        self._api = api

    async def load_list(self, *, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Load videos list payload."""
        return list(await load_videos(api=self._api, params=params))

    async def load_list_bundle(self, *, params: dict[str, Any] | None = None) -> VideosListBundle:
        """Load videos and review-summary map."""
        videos = list(await load_videos(api=self._api, params=params) or [])
        video_ids = [int(v.get("id") or 0) for v in videos if int(v.get("id") or 0) > 0]
        review_summary_by_video_id: dict[int, dict[str, Any]] = {}
        if video_ids:
            summaries = await self._api.get("/videos/reviews/summary", params={"video_ids": video_ids})
            for row in list(summaries or []):
                if not isinstance(row, dict):
                    continue
                try:
                    vid = int(row.get("video_id") or 0)
                except (TypeError, ValueError):
                    continue
                if vid > 0:
                    review_summary_by_video_id[vid] = row
        return VideosListBundle(
            videos=videos,
            review_summary_by_video_id=review_summary_by_video_id,
        )

    async def create_video(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new video row."""
        return dict(await self._api.post("/videos", dict(payload or {})) or {})

    async def suggest_video_from_url(self, *, url: str) -> dict[str, Any]:
        """Resolve URL metadata suggestions for the share dialog."""
        return dict(await self._api.post("/url-preview/metadata", {"url": str(url or "").strip()}) or {})

    async def load_video(self, *, video_id: int) -> dict[str, Any]:
        """Load one video detail payload."""
        return dict(await self._api.get(f"/videos/{int(video_id)}") or {})

    async def load_video_reviews(self, *, video_id: int) -> list[dict[str, Any]]:
        """Load video reviews for the detail route."""
        return list(await self._api.get(f"/videos/{int(video_id)}/reviews") or [])

    async def save_video_review(self, *, video_id: int, rating: int, text: str) -> dict[str, Any]:
        """Create/update current user's video review."""
        out = await self._api.post(
            f"/videos/{int(video_id)}/reviews",
            {"rating": int(rating), "text": str(text or "")},
        )
        return dict(out or {})

    async def delete_video_review(self, *, video_id: int, review_id: int) -> bool:
        """Delete one video review."""
        await self._api.delete(f"/videos/{int(video_id)}/reviews/{int(review_id)}")
        return True
