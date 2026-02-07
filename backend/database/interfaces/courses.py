from __future__ import annotations

from typing import Protocol

from backend.database.models import CourseRecord


class CoursesRepository(Protocol):
    def list_courses(
        self,
        query: str | None,
        provider: str | None,
        category: str | None,
        level: str | None,
    ) -> list[CourseRecord]:
        """List courses with optional filters."""

    def get_course_by_id(self, course_id: int) -> CourseRecord | None:
        """Fetch a course by ID."""

    def create_course(
        self,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
        created_at: str,
    ) -> int:
        """Create a course."""

    def update_course(
        self,
        course_id: int,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
    ) -> int:
        """Update a course."""

    def delete_course(self, course_id: int) -> int:
        """Delete a course by ID."""
