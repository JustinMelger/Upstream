from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass
from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.path_recommendations import PathRecommendationsRepository
from backend.database.tx import session_scope


class PathRecommendationsServiceError(ServiceError):
    """Domain error for path recommendation failures."""


def path_recommendations_error_handler(
    message: str = "An unexpected error occurred while handling path recommendations",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Build an error-handler decorator for path recommendation methods.

    Args:
        message: Default fallback error message.
        status_code: Default HTTP status code for unexpected failures.

    Returns:
        Decorator wrapping uncaught errors as `PathRecommendationsServiceError`.

    """
    return error_handler(
        service_error=PathRecommendationsServiceError,
        message=message,
        status_code=status_code,
        log_message="Path recommendations service error",
    )


@dataclass
class PathRecommendationMutationPayload:
    """Typed service-layer payload for path recommendation mutation."""

    note: str | None = None


class PathRecommendationsService:
    """Path recommendations service."""

    def __init__(self, repo: PathRecommendationsRepository):
        """Initialize the service.

        Args:
            repo: Path recommendations repository.

        """
        self._repo = repo

    @path_recommendations_error_handler()
    async def list_recommendations(self, *, path_id: int) -> list[dict]:
        """List recommendation rows for one path.

        Args:
            path_id: Path identifier.

        Returns:
            Serialized recommendation rows.

        """
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_path(path_id=path_id)
        return [
            {
                "id": r.id,
                "path_id": r.path_id,
                "note": r.note or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @path_recommendations_error_handler()
    async def create_recommendation(self, *, path_id: int, payload: dict, created_by: str) -> dict:
        """Create/update current user's recommendation for a path."""
        data = self._parse_mutation_payload(payload)
        note = str(data.note or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()

        recommendation_id: int | None = None
        async with session_scope(self._repo.session):
            existing = await self._repo.get_recommendation_for_path_by_user(path_id=int(path_id), created_by=str(created_by))
            if existing:
                await self._repo.update_recommendation(
                    recommendation_id=existing.id,
                    note=note,
                    created_at=created_at,
                )
                recommendation_id = existing.id
            else:
                try:
                    recommendation_id = await self._repo.create_recommendation(
                        path_id=int(path_id),
                        note=note,
                        created_by=str(created_by),
                        created_at=created_at,
                    )
                except IntegrityError:
                    concurrent = await self._repo.get_recommendation_for_path_by_user(
                        path_id=int(path_id), created_by=str(created_by)
                    )
                    if not concurrent:
                        raise
                    await self._repo.update_recommendation(
                        recommendation_id=concurrent.id,
                        note=note,
                        created_at=created_at,
                    )
                    recommendation_id = concurrent.id

        async with session_scope(self._repo.session):
            row = await self._repo.get_recommendation_by_id(int(recommendation_id or 0))
        if not row:
            raise PathRecommendationsServiceError(detail="create_failed", status_code=500)
        return {
            "id": row.id,
            "path_id": row.path_id,
            "note": row.note or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> PathRecommendationMutationPayload:
        """Parse and validate a path recommendation payload."""
        try:
            return PathRecommendationMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise PathRecommendationsServiceError(detail="invalid_payload", status_code=400) from exc

    @path_recommendations_error_handler()
    async def get_recommendation_by_id(self, *, recommendation_id: int) -> dict | None:
        """Fetch recommendation by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_recommendation_by_id(int(recommendation_id))
        if not row:
            return None
        return {
            "id": row.id,
            "path_id": row.path_id,
            "note": row.note or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @path_recommendations_error_handler()
    async def delete_recommendation(self, *, recommendation_id: int) -> bool:
        """Delete recommendation by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_recommendation(recommendation_id=int(recommendation_id))
        return bool(deleted)

    @path_recommendations_error_handler()
    async def summaries(self, *, path_ids: list[int]) -> list[dict]:
        """Return recommendation count summary for path ids."""
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
            counts = await self._repo.recommendation_count_for_paths(path_ids=unique_ids)

        return [{"path_id": pid, "recommendation_count": int(counts.get(pid, 0))} for pid in unique_ids]
