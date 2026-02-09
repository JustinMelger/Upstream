from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import courses_error_handler, CoursesServiceError
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.models import CourseRecord


class CoursesService:
    """Course management service."""

    def __init__(self, repo: CoursesRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for courses.
        """
        self._repo = repo

    @courses_error_handler()
    async def list_courses(
        self,
        *,
        query: str | None = None,
        provider: str | None = None,
        category: str | None = None,
        level: str | None = None,
    ) -> list[dict]:
        """List courses with optional filters.

        Args:
            query: Search query.
            provider: Provider filter.
            category: Category filter.
            level: Level filter.

        Returns:
            Course list payloads.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_courses(query=query, provider=provider, category=category, level=level)
        return [self._to_payload(row) for row in rows]

    @courses_error_handler()
    async def get_course_by_id(self, course_id: int) -> dict | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course payload or None if missing.
        """
        async with self._repo.session.begin():
            course = await self._repo.get_course_by_id(course_id)
        return self._to_payload(course) if course else None

    @courses_error_handler()
    async def create_course(self, payload: dict) -> dict:
        """Create a new course.

        Args:
            payload: Course payload.

        Returns:
            Created course payload.

        Raises:
            CoursesServiceError: If required fields are missing.
        """
        title = (payload.get("title") or "").strip()
        if not title:
            raise CoursesServiceError(detail="missing_title", status_code=400)

        provider = (payload.get("provider") or "").strip() or None
        category = (payload.get("category") or "").strip() or None
        level = (payload.get("level") or "").strip() or None
        url = (payload.get("url") or "").strip() or None
        duration_hours = self._parse_float(payload.get("duration_hours"))
        created_at = datetime.now(timezone.utc).isoformat()

        async with self._repo.session.begin():
            course_id = await self._repo.create_course(
                title=title,
                provider=provider,
                category=category,
                level=level,
                duration_hours=duration_hours,
                url=url,
                created_at=created_at,
            )
        course = await self.get_course_by_id(course_id)
        if not course:
            raise CoursesServiceError(detail="created_course_missing", status_code=500)
        return course

    @courses_error_handler()
    async def update_course(self, course_id: int, payload: dict) -> dict | None:
        """Update a course by ID.

        Args:
            course_id: Course ID.
            payload: Updates payload.

        Returns:
            Updated course payload or None if missing.
        """
        async with self._repo.session.begin():
            existing = await self._repo.get_course_by_id(course_id)
        if not existing:
            return None

        title = (payload.get("title") or existing.title).strip()
        provider = (payload.get("provider") or (existing.provider or "")).strip() or None
        category = (payload.get("category") or (existing.category or "")).strip() or None
        level = (payload.get("level") or (existing.level or "")).strip() or None
        url = (payload.get("url") or (existing.url or "")).strip() or None
        duration_hours = self._parse_float(payload.get("duration_hours"))
        if duration_hours is None:
            duration_hours = existing.duration_hours

        async with self._repo.session.begin():
            await self._repo.update_course(
                course_id=course_id,
                title=title,
                provider=provider,
                category=category,
                level=level,
                duration_hours=duration_hours,
                url=url,
            )
        return await self.get_course_by_id(course_id)

    @courses_error_handler()
    async def delete_course(self, course_id: int) -> bool:
        """Delete a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            True if deleted.
        """
        async with self._repo.session.begin():
            return (await self._repo.delete_course(course_id)) > 0

    @staticmethod
    def _parse_float(value):
        """Parse a float value or return None."""
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None

    @staticmethod
    def _to_payload(course: CourseRecord) -> dict:
        """Convert a course record to an API payload."""
        return {
            "id": course.id,
            "title": course.title or "",
            "provider": course.provider or "",
            "category": course.category or "",
            "level": course.level or "",
            "duration_hours": course.duration_hours,
            "url": course.url or "",
            "created_at": course.created_at,
        }
