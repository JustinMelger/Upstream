from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.video_reviews import VideoReviewsRepository
from backend.database.tx import session_scope
from backend.services.review_upsert import upsert_review_id


class VideoReviewsServiceError(ServiceError):
    """Domain error for video review failures."""


def video_reviews_error_handler(
    message: str = "An unexpected error occurred while handling video reviews",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Build an error-handler decorator for video review service methods."""
    return error_handler(
        service_error=VideoReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Video reviews service error",
    )


@dataclass
class VideoReviewMutationPayload:
    """Typed service-layer payload for video review mutation."""

    rating: int | float | str | None = None
    text: str | None = None


class VideoReviewsService:
    """Video reviews service."""

    def __init__(self, repo: VideoReviewsRepository):
        """Initialize the service.

        Args:
            repo: Video reviews repository.

        """
        self._repo = repo

    @staticmethod
    def _coerce_rating(value: int | float | str | None) -> int:
        if value is None:
            raise VideoReviewsServiceError(detail="invalid_rating", status_code=400)
        try:
            rating_i = int(value)
        except (TypeError, ValueError):
            raise VideoReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise VideoReviewsServiceError(detail="invalid_rating", status_code=400)
        return rating_i

    @video_reviews_error_handler()
    async def list_reviews(self, *, video_id: int) -> list[dict]:
        """List review rows for one video."""
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_video(video_id=video_id)
        return [
            {
                "id": r.id,
                "video_id": r.video_id,
                "rating": r.rating,
                "text": r.text or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @video_reviews_error_handler()
    async def create_review(self, *, video_id: int, payload: dict, created_by: str) -> dict:
        """Create or update the current user's review for a video."""
        data = self._parse_mutation_payload(payload)
        rating_i = self._coerce_rating(data.rating)

        text = str(data.text or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            review_id = await upsert_review_id(
                get_existing=lambda: self._repo.get_review_for_video_by_user(
                    video_id=int(video_id),
                    created_by=str(created_by),
                ),
                create=lambda: self._repo.create_review(
                    video_id=int(video_id),
                    rating=rating_i,
                    text=text,
                    created_by=str(created_by),
                    created_at=created_at,
                ),
                get_concurrent=lambda: self._repo.get_review_for_video_by_user(
                    video_id=int(video_id),
                    created_by=str(created_by),
                ),
                update=lambda review_id: self._repo.update_review(
                    review_id=int(review_id),
                    rating=rating_i,
                    text=text,
                    created_at=created_at,
                ),
            )

        async with session_scope(self._repo.session):
            created = await self._repo.get_review_by_id(int(review_id))
        if not created:
            raise VideoReviewsServiceError(detail="create_failed", status_code=500)
        return {
            "id": created.id,
            "video_id": created.video_id,
            "rating": created.rating,
            "text": created.text or "",
            "created_by": created.created_by,
            "created_at": created.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> VideoReviewMutationPayload:
        """Parse and validate a video review payload."""
        try:
            return VideoReviewMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise VideoReviewsServiceError(detail="invalid_payload", status_code=400) from exc

    @video_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_review_by_id(int(review_id))
        if not row:
            return None
        return {
            "id": row.id,
            "video_id": row.video_id,
            "rating": row.rating,
            "text": row.text or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @video_reviews_error_handler()
    async def delete_review(self, *, review_id: int) -> bool:
        """Delete a review by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)

    @video_reviews_error_handler()
    async def summaries(self, *, video_ids: list[int]) -> list[dict]:
        """Return review summaries for the given video ids."""
        unique_ids: list[int] = []
        seen: set[int] = set()
        for vid in list(video_ids or []):
            try:
                vid_i = int(vid)
            except (TypeError, ValueError):
                continue
            if vid_i <= 0 or vid_i in seen:
                continue
            seen.add(vid_i)
            unique_ids.append(vid_i)

        async with session_scope(self._repo.session):
            summary_map = await self._repo.summaries_for_videos(video_ids=unique_ids)

        out: list[dict] = []
        for vid in unique_ids:
            avg, count = summary_map.get(vid, (0.0, 0))
            out.append({"video_id": vid, "avg_rating": float(avg), "review_count": int(count)})
        return out
