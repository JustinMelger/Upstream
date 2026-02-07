from __future__ import annotations

from backend.database.db import database
from backend.database.interfaces import PathsRepository
from backend.database.models import PathCourseRecord, PathRecord
from backend.database.paths_repository import SQLitePathsRepository


class PathsService:
    """Learning paths management service."""

    def __init__(self, repo: PathsRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for paths.
        """
        self._repo = repo

    def list_paths(self) -> list[dict]:
        """List all learning paths.

        Returns:
            Path list payloads.
        """
        return [self._path_payload(path) for path in self._repo.list_paths()]

    def get_path(self, path_id: int) -> dict | None:
        """Fetch a path and its courses by ID.

        Args:
            path_id: Path ID.

        Returns:
            Path payload or None if missing.
        """
        result = self._repo.get_path(path_id)
        if not result:
            return None
        path, courses = result
        return {
            "id": path.id,
            "name": path.name,
            "description": path.description or "",
            "courses": [self._course_payload(course) for course in courses],
        }

    def create_path(self, payload: dict) -> dict:
        """Create a learning path with ordered courses.

        Args:
            payload: Path payload with course_ids.

        Returns:
            Created path payload.

        Raises:
            ValueError: If required fields are missing or the name is duplicate.
        """
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("missing_name")
        description = (payload.get("description") or "").strip() or None
        course_ids = payload.get("course_ids") or []

        if self._repo.path_name_exists(name):
            raise ValueError("duplicate_name")

        path_id = self._repo.create_path(name, description)
        self._repo.delete_path_courses(path_id)
        self._repo.set_path_courses(path_id, [int(course_id) for course_id in course_ids])
        return self.get_path(path_id) or {"error": "not_found"}

    def update_path(self, path_id: int, payload: dict) -> dict:
        """Update a learning path and its course ordering.

        Args:
            path_id: Path ID.
            payload: Path updates and course_ids order.

        Returns:
            Updated path payload.

        Raises:
            ValueError: If required fields are missing or the name is duplicate.
        """
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("missing_name")
        description = (payload.get("description") or "").strip() or None
        course_ids = payload.get("course_ids") or []

        if self._repo.path_name_exists_for_other_id(path_id, name):
            raise ValueError("duplicate_name")

        self._repo.update_path(path_id, name, description)
        self._repo.delete_path_courses(path_id)
        self._repo.set_path_courses(path_id, [int(course_id) for course_id in course_ids])
        return self.get_path(path_id) or {"error": "not_found"}

    def delete_path(self, path_id: int) -> bool:
        """Delete a learning path by ID.

        Args:
            path_id: Path ID.

        Returns:
            True if deleted.
        """
        self._repo.delete_path_courses(path_id)
        return self._repo.delete_path(path_id) > 0

    @staticmethod
    def _path_payload(path: PathRecord) -> dict:
        return {"id": path.id, "name": path.name, "description": path.description or ""}

    @staticmethod
    def _course_payload(course: PathCourseRecord) -> dict:
        return {
            "id": course.id,
            "title": course.title or "",
            "provider": course.provider or "",
            "category": course.category or "",
            "level": course.level or "",
            "duration_hours": course.duration_hours,
            "url": course.url or "",
        }


paths_service = PathsService(SQLitePathsRepository(database))
