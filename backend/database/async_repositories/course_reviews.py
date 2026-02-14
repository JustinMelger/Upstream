from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CourseReviewRecord
from backend.database.orm_models import CourseReview as CourseReviewModel


class CourseReviewsRepository:
    """Async SQLAlchemy implementation of course review persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_for_course(self, *, course_id: int) -> list[CourseReviewRecord]:
        """List reviews for a course (newest first)."""
        result = await self.session.execute(
            select(CourseReviewModel).where(CourseReviewModel.course_id == course_id).order_by(CourseReviewModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            CourseReviewRecord(
                id=int(r.id),
                course_id=int(r.course_id),
                rating=int(r.rating),
                text=r.text,
                created_by=str(r.created_by),
                created_at=str(r.created_at),
            )
            for r in rows
        ]

    async def create_review(
        self,
        *,
        course_id: int,
        rating: int,
        text: str | None,
        created_by: str,
        created_at: str,
    ) -> int:
        """Create a review and return its id."""
        row = CourseReviewModel(
            course_id=int(course_id),
            rating=int(rating),
            text=text,
            created_by=str(created_by),
            created_at=str(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_review_for_course_by_user(self, *, course_id: int, created_by: str) -> CourseReviewRecord | None:
        """Fetch a review by (course_id, created_by)."""
        result = await self.session.execute(
            select(CourseReviewModel)
            .where(CourseReviewModel.course_id == int(course_id))
            .where(CourseReviewModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseReviewRecord(
            id=int(row.id),
            course_id=int(row.course_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=str(row.created_at),
        )

    async def update_review(
        self,
        *,
        review_id: int,
        rating: int,
        text: str | None,
        created_at: str,
    ) -> int:
        """Update a review.

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(CourseReviewModel)
            .where(CourseReviewModel.id == int(review_id))
            .values(rating=int(rating), text=text, created_at=str(created_at))
        )
        return int(result.rowcount or 0)

    async def delete_review(self, *, review_id: int) -> int:
        """Delete a review by id.

        Returns:
            Number of rows deleted.
        """
        result = await self.session.execute(delete(CourseReviewModel).where(CourseReviewModel.id == int(review_id)))
        return int(result.rowcount or 0)

    async def summaries_for_courses(self, *, course_ids: list[int]) -> dict[int, tuple[float, int]]:
        """Return (avg_rating, count) per course id for the given ids."""
        if not course_ids:
            return {}
        result = await self.session.execute(
            select(
                CourseReviewModel.course_id,
                func.avg(CourseReviewModel.rating),
                func.count(CourseReviewModel.id),
            )
            .where(CourseReviewModel.course_id.in_([int(i) for i in course_ids]))
            .group_by(CourseReviewModel.course_id)
        )
        out: dict[int, tuple[float, int]] = {}
        for course_id, avg_rating, count in result.all():
            try:
                out[int(course_id)] = (float(avg_rating or 0.0), int(count or 0))
            except (TypeError, ValueError):
                continue
        return out

    async def get_review_by_id(self, review_id: int) -> CourseReviewRecord | None:
        """Fetch a review by id."""
        result = await self.session.execute(select(CourseReviewModel).where(CourseReviewModel.id == review_id).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseReviewRecord(
            id=int(row.id),
            course_id=int(row.course_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=str(row.created_at),
        )
