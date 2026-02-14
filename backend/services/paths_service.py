from __future__ import annotations

from backend.core.errors import paths_error_handler, PathsServiceError
from backend.database.async_repositories.paths import PathsRepository
from backend.database.models import PathCourseRecord, PathRecord


class PathsService:
    """Learning paths management service."""

    def __init__(self, repo: PathsRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for paths.
        """
        self._repo = repo

    @paths_error_handler()
    async def list_paths(self) -> list[dict]:
        """List all learning paths.

        Returns:
            Path list payloads.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_paths()
        return [self._path_payload(path) for path in rows]

    @paths_error_handler()
    async def get_path(self, path_id: int) -> dict | None:
        """Fetch a path and its courses by ID.

        Args:
            path_id: Path ID.

        Returns:
            Path payload or None if missing.
        """
        async with self._repo.session.begin():
            result = await self._repo.get_path(path_id)
        if not result:
            return None
        path, courses = result
        return {
            "id": path.id,
            "name": path.name,
            "description": path.description or "",
            "created_by": path.created_by,
            "courses": [self._course_payload(course) for course in courses],
        }

    @paths_error_handler()
    async def create_path(self, payload: dict) -> dict:
        """Create a learning path with ordered courses.

        Args:
            payload: Path payload with course_ids.

        Returns:
            Created path payload.

        Raises:
            PathsServiceError: If required fields are missing or the name is duplicate.
        """
        name = (payload.get("name") or "").strip()
        if not name:
            raise PathsServiceError(detail="missing_name", status_code=400)
        description = (payload.get("description") or "").strip() or None
        course_ids = payload.get("course_ids") or []
        created_by = (payload.get("created_by") or "").strip() or None

        async with self._repo.session.begin():
            if await self._repo.path_name_exists(name):
                raise PathsServiceError(detail="duplicate_name", status_code=409)
            path_id = await self._repo.create_path_with_courses(
                name,
                description,
                [int(course_id) for course_id in course_ids],
                created_by,
            )
        path = await self.get_path(path_id)
        if not path:
            raise PathsServiceError(detail="created_path_missing", status_code=500)
        return path

    @paths_error_handler()
    async def update_path(self, path_id: int, payload: dict) -> dict:
        """Update a learning path and its course ordering.

        Args:
            path_id: Path ID.
            payload: Path updates and course_ids order.

        Returns:
            Updated path payload.

        Raises:
            PathsServiceError: If required fields are missing or the name is duplicate.
        """
        name = (payload.get("name") or "").strip()
        if not name:
            raise PathsServiceError(detail="missing_name", status_code=400)
        description = (payload.get("description") or "").strip() or None
        course_ids = payload.get("course_ids") or []

        async with self._repo.session.begin():
            if await self._repo.path_name_exists_for_other_id(path_id, name):
                raise PathsServiceError(detail="duplicate_name", status_code=409)
            await self._repo.update_path_with_courses(path_id, name, description, [int(course_id) for course_id in course_ids])
        path = await self.get_path(path_id)
        if not path:
            raise PathsServiceError(detail="path_not_found", status_code=404)
        return path

    @paths_error_handler()
    async def delete_path(self, path_id: int) -> bool:
        """Delete a learning path by ID.

        Args:
            path_id: Path ID.

        Returns:
            True if deleted.
        """
        async with self._repo.session.begin():
            return (await self._repo.delete_path_with_courses(path_id)) > 0

    @staticmethod
    def _path_payload(path: PathRecord) -> dict:
        """Convert a path record into an API payload."""
        return {"id": path.id, "name": path.name, "description": path.description or "", "created_by": path.created_by}

    @staticmethod
    def _course_payload(course: PathCourseRecord) -> dict:
        """Convert a path course record into an API payload."""
        return {
            "id": course.id,
            "title": course.title or "",
            "provider": course.provider or "",
            "category": course.category or "",
            "level": course.level or "",
            "duration_hours": course.duration_hours,
            "url": course.url or "",
        }
