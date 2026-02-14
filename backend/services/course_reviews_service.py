from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, ServiceError
from backend.database.async_repositories.course_reviews import CourseReviewsRepository


class CourseReviewsServiceError(ServiceError):
    """Domain error for course review failures."""


def course_reviews_error_handler(
    message: str = "An unexpected error occurred while handling course reviews",
    status_code: int = 500,
):
    return error_handler(
        service_error=CourseReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Course reviews service error",
    )


class CourseReviewsService:
    """Course reviews service."""

    def __init__(self, repo: CourseReviewsRepository):
        self._repo = repo

    @course_reviews_error_handler()
    async def list_reviews(self, *, course_id: int) -> list[dict]:
        async with self._repo.session.begin():
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
        rating = payload.get("rating")
        try:
            rating_i = int(rating)
        except (TypeError, ValueError):
            raise CourseReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise CourseReviewsServiceError(detail="invalid_rating", status_code=400)

        text = str(payload.get("text") or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()

        review_id: int | None = None
        async with self._repo.session.begin():
            existing = await self._repo.get_review_for_course_by_user(course_id=int(course_id), created_by=str(created_by))
            if existing:
                await self._repo.update_review(review_id=existing.id, rating=rating_i, text=text, created_at=created_at)
                review_id = existing.id
            else:
                try:
                    review_id = await self._repo.create_review(
                        course_id=int(course_id),
                        rating=rating_i,
                        text=text,
                        created_by=str(created_by),
                        created_at=created_at,
                    )
                except IntegrityError:
                    # Concurrent insert: fetch then update.
                    concurrent = await self._repo.get_review_for_course_by_user(
                        course_id=int(course_id), created_by=str(created_by)
                    )
                    if not concurrent:
                        raise
                    await self._repo.update_review(
                        review_id=concurrent.id,
                        rating=rating_i,
                        text=text,
                        created_at=created_at,
                    )
                    review_id = concurrent.id

        async with self._repo.session.begin():
            created = await self._repo.get_review_by_id(int(review_id or 0))
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

    @course_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with self._repo.session.begin():
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
        async with self._repo.session.begin():
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)

    @course_reviews_error_handler()
    async def summaries(self, *, course_ids: list[int]) -> list[dict]:
        """Return review summaries for the given course ids."""
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

        async with self._repo.session.begin():
            summary_map = await self._repo.summaries_for_courses(course_ids=unique_ids)

        out: list[dict] = []
        for cid in unique_ids:
            avg, count = summary_map.get(cid, (0.0, 0))
            out.append({"course_id": cid, "avg_rating": float(avg), "review_count": int(count)})
        return out
