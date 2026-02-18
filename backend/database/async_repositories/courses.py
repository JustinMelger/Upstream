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
                | func.lower(func.coalesce(CourseModel.learning_outcomes, "")).like(like)
                | func.lower(func.coalesce(CourseModel.prerequisites, "")).like(like)
                | func.lower(func.coalesce(CourseModel.language, "")).like(like)
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
                learning_outcomes=row.learning_outcomes,
                prerequisites=row.prerequisites,
                language=row.language,
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
            learning_outcomes=row.learning_outcomes,
            prerequisites=row.prerequisites,
            language=row.language,
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
        learning_outcomes: str | None,
        prerequisites: str | None,
        language: str | None,
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
            learning_outcomes=learning_outcomes,
            prerequisites=prerequisites,
            language=language,
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

    async def find_course_by_url(self, *, url: str) -> CourseRecord | None:
        """Find a course by normalized URL (trimmed + lowercase exact match)."""
        normalized = (url or "").strip().lower()
        if not normalized:
            return None
        stmt = (
            select(CourseModel)
            .where(CourseModel.url.is_not(None))
            .where(func.lower(func.trim(CourseModel.url)) == normalized)
            .order_by(CourseModel.id.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseRecord(
            id=row.id,
            title=row.title or "",
            description=row.description or "",
            learning_outcomes=row.learning_outcomes,
            prerequisites=row.prerequisites,
            language=row.language,
            provider=row.provider,
            category=row.category,
            level=row.level,
            duration_hours=row.duration_hours,
            url=row.url,
            created_at=row.created_at,
            created_by=row.created_by,
        )

    async def find_course_by_title_provider(self, *, title: str, provider: str | None) -> CourseRecord | None:
        """Find a course by normalized title + provider (trimmed + lowercase exact match)."""
        normalized_title = (title or "").strip().lower()
        normalized_provider = (provider or "").strip().lower()
        if not normalized_title:
            return None
        stmt = select(CourseModel).where(func.lower(func.trim(CourseModel.title)) == normalized_title)
        if normalized_provider:
            stmt = stmt.where(func.lower(func.trim(func.coalesce(CourseModel.provider, ""))) == normalized_provider)
        else:
            stmt = stmt.where(func.trim(func.coalesce(CourseModel.provider, "")) == "")
        stmt = stmt.order_by(CourseModel.id.asc()).limit(1)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CourseRecord(
            id=row.id,
            title=row.title or "",
            description=row.description or "",
            learning_outcomes=row.learning_outcomes,
            prerequisites=row.prerequisites,
            language=row.language,
            provider=row.provider,
            category=row.category,
            level=row.level,
            duration_hours=row.duration_hours,
            url=row.url,
            created_at=row.created_at,
            created_by=row.created_by,
        )

    async def update_course(
        self,
        *,
        course_id: int,
        title: str,
        description: str,
        learning_outcomes: str | None,
        prerequisites: str | None,
        language: str | None,
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
                learning_outcomes=learning_outcomes,
                prerequisites=prerequisites,
                language=language,
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
