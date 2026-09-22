from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.course_reviews import CourseReviewsRepository
from backend.database.tx import session_scope
from backend.services.review_upsert import upsert_review_id


class CourseReviewsServiceError(ServiceError):
    """Domain error for course review failures."""


def course_reviews_error_handler(
    message: str = "An unexpected error occurred while handling course reviews",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Build an error-handler decorator for course review methods.

    Args:
        message: Default fallback error message.
        status_code: Default HTTP status code for unexpected failures.

    Returns:
        Decorator wrapping uncaught errors as `CourseReviewsServiceError`.

    """
    return error_handler(
        service_error=CourseReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Course reviews service error",
    )


@dataclass
class CourseReviewMutationPayload:
    """Typed service-layer payload for course review mutation."""

    rating: int | float | str | None = None
    text: str | None = None


class CourseReviewsService:
    """Course reviews service."""

    def __init__(self, repo: CourseReviewsRepository):
        """Initialize the service.

        Args:
            repo: Course reviews repository.

        """
        self._repo = repo

    @staticmethod
    def _coerce_rating(value: int | float | str | None) -> int:
        if value is None:
            raise CourseReviewsServiceError(detail="invalid_rating", status_code=400)
        try:
            rating_i = int(value)
        except (TypeError, ValueError):
            raise CourseReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise CourseReviewsServiceError(detail="invalid_rating", status_code=400)
        return rating_i

    @course_reviews_error_handler()
    async def list_reviews(self, *, course_id: int) -> list[dict]:
        """List review rows for one course.

        Args:
            course_id: Course identifier.

        Returns:
            Serialized review rows.

        """
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_course(course_id=course_id)
        return [
            {
                "id": r.id,
                "course_id": r.course_id,
                "rating": r.rating,
                "text": r.text or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @course_reviews_error_handler()
    async def create_review(self, *, course_id: int, payload: dict, created_by: str) -> dict:
        """Create or update the current user's review for a course.

        Posting a review again updates the existing review (one review per user
        per course).
        """
        data = self._parse_mutation_payload(payload)
        rating_i = self._coerce_rating(data.rating)

        text = str(data.text or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            review_id = await upsert_review_id(
                get_existing=lambda: self._repo.get_review_for_course_by_user(
                    course_id=int(course_id),
                    created_by=str(created_by),
                ),
                create=lambda: self._repo.create_review(
                    course_id=int(course_id),
                    rating=rating_i,
                    text=text,
                    created_by=str(created_by),
                    created_at=created_at,
                ),
                get_concurrent=lambda: self._repo.get_review_for_course_by_user(
                    course_id=int(course_id),
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
            raise CourseReviewsServiceError(detail="create_failed", status_code=500)
        return {
            "id": created.id,
            "course_id": created.course_id,
            "rating": created.rating,
            "text": created.text or "",
            "created_by": created.created_by,
            "created_at": created.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> CourseReviewMutationPayload:
        """Parse and validate a course review payload."""
        try:
            return CourseReviewMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise CourseReviewsServiceError(detail="invalid_payload", status_code=400) from exc

    @course_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_review_by_id(int(review_id))
        if not row:
            return None
        return {
            "id": row.id,
            "course_id": row.course_id,
            "rating": row.rating,
            "text": row.text or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @course_reviews_error_handler()
    async def delete_review(self, *, review_id: int) -> bool:
        """Delete a review by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)
