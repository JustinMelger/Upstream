from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import CourseRecord
from backend.database.orm_models import Course as CourseModel, PathItem


class CoursesRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of courses persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def set_recommendation_note(self, content_id: int, note: str | None) -> None:
        """Persist an explicitly supplied sharing note."""
        await self.session.execute(update(CourseModel).where(CourseModel.id == content_id).values(recommendation_note=note))

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
            created_at=self._as_iso(row.created_at),
            recommendation_note=row.recommendation_note,
            created_by=row.created_by,
        )

    async def create_course(self, *, payload: "CreateCoursePayload") -> int:
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
            title=payload.title,
            description=payload.description,
            learning_outcomes=payload.learning_outcomes,
            prerequisites=payload.prerequisites,
            language=payload.language,
            provider=payload.provider,
            category=payload.category,
            level=payload.level,
            duration_hours=payload.duration_hours,
            url=payload.url,
            created_at=self._as_datetime(payload.created_at),
            created_by=payload.created_by,
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
            created_at=self._as_iso(row.created_at),
            recommendation_note=row.recommendation_note,
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
            created_at=self._as_iso(row.created_at),
            recommendation_note=row.recommendation_note,
            created_by=row.created_by,
        )

    async def update_course(self, *, payload: "UpdateCoursePayload") -> int:
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
            .where(CourseModel.id == payload.course_id)
            .values(
                title=payload.title,
                description=payload.description,
                learning_outcomes=payload.learning_outcomes,
                prerequisites=payload.prerequisites,
                language=payload.language,
                provider=payload.provider,
                category=payload.category,
                level=payload.level,
                duration_hours=payload.duration_hours,
                url=payload.url,
            )
        )
        return self._rowcount(result)

    async def delete_course(self, course_id: int) -> int:
        """Delete a course.

        Args:
            course_id: Course ID.

        Returns:
            Number of rows deleted.
        """
        await self.session.execute(delete(PathItem).where(PathItem.item_type == "course", PathItem.item_id == course_id))
        result = await self.session.execute(delete(CourseModel).where(CourseModel.id == course_id))
        return self._rowcount(result)


@dataclass(frozen=True, slots=True)
class CreateCoursePayload:
    """Typed input for course creation writes."""

    title: str
    description: str
    learning_outcomes: str | None
    prerequisites: str | None
    language: str | None
    provider: str | None
    category: str | None
    level: str | None
    duration_hours: float | None
    url: str | None
    created_at: str | datetime | None
    created_by: str | None


@dataclass(frozen=True, slots=True)
class UpdateCoursePayload:
    """Typed input for course update writes."""

    course_id: int
    title: str
    description: str
    learning_outcomes: str | None
    prerequisites: str | None
    language: str | None
    provider: str | None
    category: str | None
    level: str | None
    duration_hours: float | None
    url: str | None
