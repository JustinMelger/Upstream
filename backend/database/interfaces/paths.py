from __future__ import annotations

from typing import Protocol

from backend.database.models import PathCourseRecord, PathRecord


class PathsRepository(Protocol):
    def list_paths(self) -> list[PathRecord]:
        """List all learning paths."""

    def get_path(self, path_id: int) -> tuple[PathRecord, list[PathCourseRecord]] | None:
        """Fetch a path and its courses by ID."""

    def create_path(self, name: str, description: str | None) -> int:
        """Create a path."""

    def path_name_exists(self, name: str) -> bool:
        """Check if a path name exists (case-insensitive)."""

    def path_name_exists_for_other_id(self, path_id: int, name: str) -> bool:
        """Check if a path name exists for a different path."""

    def set_path_courses(self, path_id: int, course_ids: list[int]) -> None:
        """Replace a path's courses with an ordered list."""

    def delete_path_courses(self, path_id: int) -> None:
        """Delete all courses for a path."""

    def update_path(self, path_id: int, name: str, description: str | None) -> int:
        """Update path metadata."""

    def delete_path(self, path_id: int) -> int:
        """Delete a path by ID."""
