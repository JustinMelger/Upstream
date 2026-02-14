from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CourseRecord
from backend.database.orm_models import Course as CourseModel


class CoursesRepository:
    """Async SQLAlchemy implementation of courses persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_courses(
        self,
        *,
        query: str | None,
        provider: str | None,
        category: str | None,
        level: str | None,
    ) -> list[CourseRecord]:
        """List courses with optional filters.

        Args:
            query: Free-text query applied to course fields.
            provider: Provider filter.
            category: Category filter.
            level: Level filter.

        Returns:
            List of course records.
        """
        stmt = select(CourseModel).order_by(CourseModel.title.asc())

        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                func.lower(CourseModel.title).like(like)
                | func.lower(func.coalesce(CourseModel.description, "")).like(like)
                | func.lower(func.coalesce(CourseModel.provider, "")).like(like)
                | func.lower(func.coalesce(CourseModel.category, "")).like(like)
                | func.lower(func.coalesce(CourseModel.level, "")).like(like)
                | func.lower(func.coalesce(CourseModel.url, "")).like(like)
            )
        if provider:
            stmt = stmt.where(CourseModel.provider == provider)
        if category:
            stmt = stmt.where(CourseModel.category == category)
        if level:
            stmt = stmt.where(CourseModel.level == level)

        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            CourseRecord(
                id=row.id,
                title=row.title or "",
                description=row.description or "",
                provider=row.provider,
                category=row.category,
                level=row.level,
                duration_hours=row.duration_hours,
                url=row.url,
                created_at=row.created_at,
                created_by=row.created_by,
            )
            for row in rows
        ]

    async def get_course_by_id(self, course_id: int) -> CourseRecord | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course record or None.
        """
        result = await self.session.execute(select(CourseModel).where(CourseModel.id == course_id).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseRecord(
            id=row.id,
            title=row.title or "",
            description=row.description or "",
            provider=row.provider,
            category=row.category,
            level=row.level,
            duration_hours=row.duration_hours,
            url=row.url,
            created_at=row.created_at,
            created_by=row.created_by,
        )

    async def create_course(
        self,
        *,
        title: str,
        description: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
        created_at: str,
        created_by: str | None,
    ) -> int:
        """Create a course.

        Args:
            title: Course title.
            provider: Course provider.
            category: Course category.
            level: Course level.
            duration_hours: Optional duration.
            url: Optional URL.
            created_at: Timestamp (ISO string).

        Returns:
            Newly created course ID.
        """
        row = CourseModel(
            title=title,
            description=description,
            provider=provider,
            category=category,
            level=level,
            duration_hours=duration_hours,
            url=url,
            created_at=created_at,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def update_course(
        self,
        *,
        course_id: int,
        title: str,
        description: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
    ) -> int:
        """Update a course.

        Args:
            course_id: Course ID.
            title: Course title.
            provider: Course provider.
            category: Course category.
            level: Course level.
            duration_hours: Optional duration.
            url: Optional URL.

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(CourseModel)
            .where(CourseModel.id == course_id)
            .values(
                title=title,
                description=description,
                provider=provider,
                category=category,
                level=level,
                duration_hours=duration_hours,
                url=url,
            )
        )
        return int(result.rowcount or 0)

    async def delete_course(self, course_id: int) -> int:
        """Delete a course.

        Args:
            course_id: Course ID.

        Returns:
            Number of rows deleted.
        """
        result = await self.session.execute(delete(CourseModel).where(CourseModel.id == course_id))
        return int(result.rowcount or 0)
