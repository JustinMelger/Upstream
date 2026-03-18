from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.videos import VideosRepository
from backend.database.models import VideoRecord
from backend.database.tx import session_scope
from backend.services.url_preview_service import UrlPreviewService


class VideosServiceError(ServiceError):
    """Domain error for video failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize a typed videos service error."""
        super().__init__(detail=detail, status_code=status_code)


def videos_error_handler(
    message: str = "An unexpected error occurred while handling videos",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Wrap uncaught video errors into a domain ServiceError."""
    return error_handler(
        service_error=VideosServiceError,
        message=message,
        status_code=status_code,
        log_message="Videos service error",
    )


@dataclass
class VideoCreatePayload:
    """Typed service-layer payload for video creation."""

    title: str | None = None
    description: str | None = None
    provider: str | None = None
    category: str | None = None
    url: str | None = None


class VideosService:
    """Application service for the Videos domain."""

    def __init__(
        self,
        repo: VideosRepository,
        url_preview_service: UrlPreviewService | None = None,
    ):
        """Initialize the videos service with repository and preview dependencies."""
        self._repo = repo
        self._url_preview_service = url_preview_service or UrlPreviewService()

    @videos_error_handler()
    async def list_videos(self, *, query: str | None, provider: str | None, category: str | None) -> list[dict]:
        """List videos."""
        async with session_scope(self._repo.session):
            rows = await self._repo.list_videos(query=query, provider=provider, category=category)
        preview_map = await self._resolve_preview_images(rows)
        return [self._to_payload(row, preview_image_url=preview_map.get(int(row.id), "")) for row in rows]

    @videos_error_handler()
    async def get_video_by_id(self, *, video_id: int) -> dict | None:
        """Fetch one video payload."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_video_by_id(int(video_id))
        if not row:
            return None
        preview_map = await self._resolve_preview_images([row])
        return self._to_payload(row, preview_image_url=preview_map.get(int(row.id), ""))

    @videos_error_handler()
    async def create_video(self, *, payload: dict, created_by: str) -> dict:
        """Create a new video."""
        data = self._parse_create_payload(payload)
        title = str(data.title or "").strip()
        description = str(data.description or "").strip()
        provider = str(data.provider or "").strip() or None
        category = str(data.category or "").strip() or None
        url = str(data.url or "").strip()

        if not title:
            raise VideosServiceError(detail="missing_title", status_code=400)
        if not description:
            raise VideosServiceError(detail="missing_description", status_code=400)
        if not url:
            raise VideosServiceError(detail="missing_url", status_code=400)
        if not (url.startswith("http://") or url.startswith("https://")):
            raise VideosServiceError(detail="invalid_url", status_code=400)

        async with session_scope(self._repo.session):
            duplicate = await self._repo.find_video_by_url(url=url)
            if duplicate:
                raise VideosServiceError(detail="duplicate_url", status_code=409)
            video_id = await self._repo.create_video(
                title=title,
                description=description,
                provider=provider,
                category=category,
                url=url,
                created_by=str(created_by),
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        created = await self.get_video_by_id(video_id=video_id)
        if not created:
            raise VideosServiceError(detail="create_failed", status_code=500)
        return dict(created)

    @staticmethod
    def _parse_create_payload(payload: dict) -> VideoCreatePayload:
        """Parse and validate a video create payload."""
        try:
            return VideoCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise VideosServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _to_payload(video: VideoRecord, *, preview_image_url: str = "") -> dict:
        """Convert a video record to an API payload."""
        return {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "provider": video.provider or "",
            "category": video.category or "",
            "url": video.url,
            "created_by": video.created_by,
            "created_at": video.created_at,
            "preview_image_url": str(preview_image_url or ""),
        }

    async def _resolve_preview_images(self, videos: list[VideoRecord]) -> dict[int, str]:
        out: dict[int, str] = {}
        if not videos:
            return out
        urls: dict[str, list[int]] = {}
        for row in videos:
            video_id = int(getattr(row, "id", 0) or 0)
            url = str(getattr(row, "url", "") or "").strip()
            if video_id <= 0 or not url:
                continue
            urls.setdefault(url, []).append(video_id)
        if not urls:
            return out
        resolved = await asyncio.gather(
            *(self._url_preview_service.resolve_image_url(source_url=url) for url in urls.keys()),
            return_exceptions=True,
        )
        for url, image_url in zip(urls.keys(), resolved, strict=False):
            image = "" if isinstance(image_url, Exception) else str(image_url or "")
            for video_id in urls.get(url, []):
                out[int(video_id)] = image
        return out
