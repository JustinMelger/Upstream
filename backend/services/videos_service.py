from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.videos import VideosRepository
from backend.database.models import VideoRecord
from backend.database.tx import session_scope
from backend.services.content_edit import validate_content_edit
from backend.services.recommendation_notes import normalize_note


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

    recommendation_note: str | None = None
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
    ):
        """Initialize the videos service with repository dependency."""
        self._repo = repo

    @videos_error_handler()
    async def list_videos(self, *, query: str | None, provider: str | None, category: str | None) -> list[dict]:
        """List videos."""
        async with session_scope(self._repo.session):
            rows = await self._repo.list_videos(query=query, provider=provider, category=category)
        return [self._to_payload(row) for row in rows]

    @videos_error_handler()
    async def get_video_by_id(self, *, video_id: int) -> dict | None:
        """Fetch one video payload."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_video_by_id(int(video_id))
        if not row:
            return None
        return self._to_payload(row)

    @videos_error_handler()
    async def create_video(self, *, payload: dict, created_by: str) -> dict:
        """Create a new video."""
        note = normalize_note(payload.get("recommendation_note"))
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
            await self._repo.set_recommendation_note(video_id, note)
        created = await self.get_video_by_id(video_id=video_id)
        if not created:
            raise VideosServiceError(detail="create_failed", status_code=500)
        return dict(created)

    async def update_video(self, content_id: int, payload: dict) -> dict | None:
        """Validate an edit and preserve omitted fields."""
        async with session_scope(self._repo.session):
            existing = await self._repo.get_video_by_id(content_id)
            if not existing:
                return None
            values = validate_content_edit(payload, kind="video")
            if "url" in values:
                duplicate = await self._repo.find_video_by_url(url=values["url"])
                if duplicate and duplicate.id != content_id:
                    raise VideosServiceError(detail="duplicate_url", status_code=409)
            await self._repo.update_content(content_id, values)
        return await self.get_video_by_id(video_id=content_id)

    async def delete_video(self, content_id: int) -> bool:
        """Remove content, reviews and path references transactionally."""
        async with session_scope(self._repo.session):
            return await self._repo.delete_content(content_id)

    @staticmethod
    def _parse_create_payload(payload: dict) -> VideoCreatePayload:
        """Parse and validate a video create payload."""
        try:
            return VideoCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise VideosServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _to_payload(video: VideoRecord) -> dict:
        """Convert a video record to an API payload."""
        return {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "provider": video.provider or "",
            "category": video.category or "",
            "url": video.url,
            "created_by": video.created_by,
            "recommendation_note": video.recommendation_note,
            "created_at": video.created_at,
            "preview_image_url": "",
        }
