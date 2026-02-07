from __future__ import annotations

from datetime import datetime, timezone

from backend.database.courses_repository import SQLiteCoursesRepository
from backend.database.db import database
from backend.database.interfaces import CoursesRepository
from backend.database.models import CourseRecord


class CoursesService:
    """Course management service."""

    def __init__(self, repo: CoursesRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for courses.
        """
        self._repo = repo

    def list_courses(
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
        rows = self._repo.list_courses(query=query, provider=provider, category=category, level=level)
        return [self._to_payload(row) for row in rows]

    def get_course_by_id(self, course_id: int) -> dict | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course payload or None if missing.
        """
        course = self._repo.get_course_by_id(course_id)
        return self._to_payload(course) if course else None

    def create_course(self, payload: dict) -> dict:
        """Create a new course.

        Args:
            payload: Course payload.

        Returns:
            Created course payload.

        Raises:
            ValueError: If required fields are missing.
        """
        title = (payload.get("title") or "").strip()
        if not title:
            raise ValueError("missing_title")

        provider = (payload.get("provider") or "").strip() or None
        category = (payload.get("category") or "").strip() or None
        level = (payload.get("level") or "").strip() or None
        url = (payload.get("url") or "").strip() or None
        duration_hours = self._parse_float(payload.get("duration_hours"))
        created_at = datetime.now(timezone.utc).isoformat()

        course_id = self._repo.create_course(
            title=title,
            provider=provider,
            category=category,
            level=level,
            duration_hours=duration_hours,
            url=url,
            created_at=created_at,
        )
        return self.get_course_by_id(course_id) or {"error": "not_found"}

    def update_course(self, course_id: int, payload: dict) -> dict | None:
        """Update a course by ID.

        Args:
            course_id: Course ID.
            payload: Updates payload.

        Returns:
            Updated course payload or None if missing.
        """
        existing = self._repo.get_course_by_id(course_id)
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

        self._repo.update_course(
            course_id=course_id,
            title=title,
            provider=provider,
            category=category,
            level=level,
            duration_hours=duration_hours,
            url=url,
        )
        return self.get_course_by_id(course_id)

    def delete_course(self, course_id: int) -> bool:
        """Delete a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            True if deleted.
        """
        return self._repo.delete_course(course_id) > 0

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


courses_service = CoursesService(SQLiteCoursesRepository(database))


def get_courses_service() -> CoursesService:
    """Provide the CoursesService dependency.

    Returns:
        CoursesService: Shared courses service instance.
    """
    return courses_service
