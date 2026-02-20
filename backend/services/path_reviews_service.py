from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError
from pydantic.dataclasses import dataclass
from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, ServiceError
from backend.database.async_repositories.path_reviews import PathReviewsRepository
from backend.database.tx import session_scope


class PathReviewsServiceError(ServiceError):
    """Domain error for path review failures."""


def path_reviews_error_handler(
    message: str = "An unexpected error occurred while handling path reviews",
    status_code: int = 500,
):
    return error_handler(
        service_error=PathReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Path reviews service error",
    )


@dataclass
class PathReviewMutationPayload:
    """Typed service-layer payload for path review mutation."""

    rating: int | float | str | None = None
    text: str | None = None


class PathReviewsService:
    """Path reviews service."""

    def __init__(self, repo: PathReviewsRepository):
        self._repo = repo

    @path_reviews_error_handler()
    async def list_reviews(self, *, path_id: int) -> list[dict]:
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_path(path_id=path_id)
        return [
            {
                "id": r.id,
                "path_id": r.path_id,
                "rating": r.rating,
                "text": r.text or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @path_reviews_error_handler()
    async def create_review(self, *, path_id: int, payload: dict, created_by: str) -> dict:
        """Create or update the current user's review for a path."""
        data = self._parse_mutation_payload(payload)
        rating = data.rating
        try:
            rating_i = int(rating)
        except (TypeError, ValueError):
            raise PathReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise PathReviewsServiceError(detail="invalid_rating", status_code=400)

        text = str(data.text or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()

        review_id: int | None = None
        async with session_scope(self._repo.session):
            existing = await self._repo.get_review_for_path_by_user(path_id=int(path_id), created_by=str(created_by))
            if existing:
                await self._repo.update_review(review_id=existing.id, rating=rating_i, text=text, created_at=created_at)
                review_id = existing.id
            else:
                try:
                    review_id = await self._repo.create_review(
                        path_id=int(path_id),
                        rating=rating_i,
                        text=text,
                        created_by=str(created_by),
                        created_at=created_at,
                    )
                except IntegrityError:
                    concurrent = await self._repo.get_review_for_path_by_user(path_id=int(path_id), created_by=str(created_by))
                    if not concurrent:
                        raise
                    await self._repo.update_review(
                        review_id=concurrent.id,
                        rating=rating_i,
                        text=text,
                        created_at=created_at,
                    )
                    review_id = concurrent.id

        async with session_scope(self._repo.session):
            created = await self._repo.get_review_by_id(int(review_id or 0))
        if not created:
            raise PathReviewsServiceError(detail="create_failed", status_code=500)
        return {
            "id": created.id,
            "path_id": created.path_id,
            "rating": created.rating,
            "text": created.text or "",
            "created_by": created.created_by,
            "created_at": created.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> PathReviewMutationPayload:
        """Parse and validate a path review payload."""
        try:
            return PathReviewMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise PathReviewsServiceError(detail="invalid_payload", status_code=400) from exc

    @path_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_review_by_id(int(review_id))
        if not row:
            return None
        return {
            "id": row.id,
            "path_id": row.path_id,
            "rating": row.rating,
            "text": row.text or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @path_reviews_error_handler()
    async def delete_review(self, *, review_id: int) -> bool:
        """Delete a review by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)

    @path_reviews_error_handler()
    async def summaries(self, *, path_ids: list[int]) -> list[dict]:
        """Return review summaries for the given path ids."""
        unique_ids: list[int] = []
        seen: set[int] = set()
        for pid in list(path_ids or []):
            try:
                pid_i = int(pid)
            except (TypeError, ValueError):
                continue
            if pid_i <= 0 or pid_i in seen:
                continue
            seen.add(pid_i)
            unique_ids.append(pid_i)

        async with session_scope(self._repo.session):
            summary_map = await self._repo.summaries_for_paths(path_ids=unique_ids)

        out: list[dict] = []
        for pid in unique_ids:
            avg, count = summary_map.get(pid, (0.0, 0))
            out.append({"path_id": pid, "avg_rating": float(avg), "review_count": int(count)})
        return out
