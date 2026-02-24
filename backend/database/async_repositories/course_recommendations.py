from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import CourseRecommendationRecord
from backend.database.orm_models import CourseRecommendation as CourseRecommendationModel


class CourseRecommendationsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy persistence for course recommendations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_course(self, *, course_id: int) -> list[CourseRecommendationRecord]:
        """List recommendations for a course (newest first)."""
        result = await self.session.execute(
            select(CourseRecommendationModel)
            .where(CourseRecommendationModel.course_id == int(course_id))
            .order_by(CourseRecommendationModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            CourseRecommendationRecord(
                id=int(r.id),
                course_id=int(r.course_id),
                note=r.note,
                created_by=str(r.created_by),
                created_at=self._as_iso_or_empty(r.created_at),
            )
            for r in rows
        ]

    async def list_for_courses(self, *, course_ids: list[int]) -> dict[int, list[CourseRecommendationRecord]]:
        """List recommendations for many courses grouped by course_id."""
        ids = [int(i) for i in list(course_ids or []) if int(i) > 0]
        if not ids:
            return {}
        result = await self.session.execute(
            select(CourseRecommendationModel)
            .where(CourseRecommendationModel.course_id.in_(ids))
            .order_by(CourseRecommendationModel.course_id.asc(), CourseRecommendationModel.id.desc())
        )
        grouped: dict[int, list[CourseRecommendationRecord]] = {}
        for r in result.scalars().all():
            cid = int(r.course_id)
            grouped.setdefault(cid, []).append(
                CourseRecommendationRecord(
                    id=int(r.id),
                    course_id=cid,
                    note=r.note,
                    created_by=str(r.created_by),
                    created_at=self._as_iso_or_empty(r.created_at),
                )
            )
        return grouped

    async def create_recommendation(
        self,
        *,
        course_id: int,
        note: str | None,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a recommendation and return id."""
        row = CourseRecommendationModel(
            course_id=int(course_id),
            note=note,
            created_by=str(created_by),
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_recommendation_for_course_by_user(
        self, *, course_id: int, created_by: str
    ) -> CourseRecommendationRecord | None:
        """Fetch recommendation by (course_id, created_by)."""
        result = await self.session.execute(
            select(CourseRecommendationModel)
            .where(CourseRecommendationModel.course_id == int(course_id))
            .where(CourseRecommendationModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseRecommendationRecord(
            id=int(row.id),
            course_id=int(row.course_id),
            note=row.note,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def update_recommendation(self, *, recommendation_id: int, note: str | None, created_at: str | datetime) -> int:
        """Update note/timestamp on an existing recommendation."""
        result = await self.session.execute(
            update(CourseRecommendationModel)
            .where(CourseRecommendationModel.id == int(recommendation_id))
            .values(note=note, created_at=self._as_datetime(created_at))
        )
        return self._rowcount(result)

    async def delete_recommendation(self, *, recommendation_id: int) -> int:
        """Delete recommendation by id."""
        result = await self.session.execute(
            delete(CourseRecommendationModel).where(CourseRecommendationModel.id == int(recommendation_id))
        )
        return self._rowcount(result)

    async def recommendation_count_for_courses(self, *, course_ids: list[int]) -> dict[int, int]:
        """Return recommendation counts for each course id."""
        if not course_ids:
            return {}
        result = await self.session.execute(
            select(CourseRecommendationModel.course_id, func.count(CourseRecommendationModel.id))
            .where(CourseRecommendationModel.course_id.in_([int(i) for i in course_ids]))
            .group_by(CourseRecommendationModel.course_id)
        )
        out: dict[int, int] = {}
        for course_id, count in result.all():
            try:
                out[int(course_id)] = int(count or 0)
            except (TypeError, ValueError):
                continue
        return out

    async def get_recommendation_by_id(self, recommendation_id: int) -> CourseRecommendationRecord | None:
        """Fetch recommendation by id."""
        result = await self.session.execute(
            select(CourseRecommendationModel).where(CourseRecommendationModel.id == int(recommendation_id)).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseRecommendationRecord(
            id=int(row.id),
            course_id=int(row.course_id),
            note=row.note,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )
