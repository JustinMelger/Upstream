from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass
from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.course_recommendations import CourseRecommendationsRepository
from backend.database.tx import session_scope


class CourseRecommendationsServiceError(ServiceError):
    """Domain error for course recommendation failures."""


def course_recommendations_error_handler(
    message: str = "An unexpected error occurred while handling course recommendations",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Build an error-handler decorator for course recommendation methods.

    Args:
        message: Default fallback error message.
        status_code: Default HTTP status code for unexpected failures.

    Returns:
        Decorator wrapping uncaught errors as `CourseRecommendationsServiceError`.

    """
    return error_handler(
        service_error=CourseRecommendationsServiceError,
        message=message,
        status_code=status_code,
        log_message="Course recommendations service error",
    )


@dataclass
class CourseRecommendationMutationPayload:
    """Typed service-layer payload for course recommendation mutation."""

    note: str | None = None


class CourseRecommendationsService:
    """Course recommendations service."""

    def __init__(self, repo: CourseRecommendationsRepository):
        """Initialize the service.

        Args:
            repo: Course recommendations repository.

        """
        self._repo = repo

    @course_recommendations_error_handler()
    async def list_recommendations(self, *, course_id: int) -> list[dict]:
        """List recommendation rows for one course.

        Args:
            course_id: Course identifier.

        Returns:
            Serialized recommendation rows.

        """
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_course(course_id=course_id)
        return [
            {
                "id": r.id,
                "course_id": r.course_id,
                "note": r.note or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @course_recommendations_error_handler()
    async def create_recommendation(self, *, course_id: int, payload: dict, created_by: str) -> dict:
        """Create/update current user's recommendation for a course."""
        data = self._parse_mutation_payload(payload)
        note = str(data.note or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()

        recommendation_id: int | None = None
        async with session_scope(self._repo.session):
            existing = await self._repo.get_recommendation_for_course_by_user(
                course_id=int(course_id), created_by=str(created_by)
            )
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
                        course_id=int(course_id),
                        note=note,
                        created_by=str(created_by),
                        created_at=created_at,
                    )
                except IntegrityError:
                    concurrent = await self._repo.get_recommendation_for_course_by_user(
                        course_id=int(course_id),
                        created_by=str(created_by),
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
            raise CourseRecommendationsServiceError(detail="create_failed", status_code=500)
        return {
            "id": row.id,
            "course_id": row.course_id,
            "note": row.note or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> CourseRecommendationMutationPayload:
        """Parse and validate a course recommendation payload."""
        try:
            return CourseRecommendationMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise CourseRecommendationsServiceError(detail="invalid_payload", status_code=400) from exc

    @course_recommendations_error_handler()
    async def get_recommendation_by_id(self, *, recommendation_id: int) -> dict | None:
        """Fetch recommendation by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_recommendation_by_id(int(recommendation_id))
        if not row:
            return None
        return {
            "id": row.id,
            "course_id": row.course_id,
            "note": row.note or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @course_recommendations_error_handler()
    async def delete_recommendation(self, *, recommendation_id: int) -> bool:
        """Delete recommendation by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_recommendation(recommendation_id=int(recommendation_id))
        return bool(deleted)

    @course_recommendations_error_handler()
    async def summaries(self, *, course_ids: list[int]) -> list[dict]:
        """Return recommendation count summary for course ids."""
        unique_ids: list[int] = []
        seen: set[int] = set()
        for cid in list(course_ids or []):
            try:
                cid_i = int(cid)
            except (TypeError, ValueError):
                continue
            if cid_i <= 0 or cid_i in seen:
                continue
            seen.add(cid_i)
            unique_ids.append(cid_i)

        async with session_scope(self._repo.session):
            counts = await self._repo.recommendation_count_for_courses(course_ids=unique_ids)

        return [{"course_id": cid, "recommendation_count": int(counts.get(cid, 0))} for cid in unique_ids]
