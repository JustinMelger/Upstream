from __future__ import annotations

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import paths_error_handler, PathsServiceError
from backend.database.async_repositories.paths import PathsRepository
from backend.database.models import PathLearningItemRecord, PathRecord
from backend.database.tx import session_scope


@dataclass
class PathItemMutationPayload:
    """Typed path-item reference for create/update flows."""

    type: str | None = None
    id: int | None = None
    position: int | None = None


@dataclass
class PathMutationPayload:
    """Typed service-layer payload for create/update path flows."""

    name: str | None = None
    description: str | None = None
    course_ids: list[int] | None = None
    items: list[PathItemMutationPayload] | None = None
    created_by: str | None = None


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
        async with session_scope(self._repo.session):
            rows = await self._repo.list_paths()
        return [self._path_payload(path) for path in rows]

    @paths_error_handler()
    async def get_path(self, path_id: int) -> dict | None:
        """Fetch a path and its learning items by ID.

        Args:
            path_id: Path ID.

        Returns:
            Path payload or None if missing.
        """
        async with session_scope(self._repo.session):
            result = await self._repo.get_path(path_id)
        if not result:
            return None
        path, items = result
        return {
            "id": path.id,
            "name": path.name,
            "description": path.description or "",
            "created_by": path.created_by,
            "courses": [self._course_payload(item) for item in items if item.item_type == "course"],
            "items": [self._item_payload(item) for item in items],
        }

    @paths_error_handler()
    async def create_path(self, payload: dict) -> dict:
        """Create a learning path with ordered learning items.

        Args:
            payload: Path payload with typed items or legacy course_ids.

        Returns:
            Created path payload.

        Raises:
            PathsServiceError: If required fields are missing or the name is duplicate.
        """
        data = self._parse_mutation_payload(payload)
        name = str(data.name or "").strip()
        if not name:
            raise PathsServiceError(detail="missing_name", status_code=400)
        description = str(data.description or "").strip() or None
        items = self._normalize_items_payload(data)
        created_by = str(data.created_by or "").strip() or None

        async with session_scope(self._repo.session):
            if await self._repo.path_name_exists(name):
                raise PathsServiceError(detail="duplicate_name", status_code=409)
            if await self._repo.has_missing_learning_items(items):
                raise PathsServiceError(detail="invalid_item_refs", status_code=400)
            path_id = await self._repo.create_path_with_items(name, description, items, created_by)
        path = await self.get_path(path_id)
        if not path:
            raise PathsServiceError(detail="created_path_missing", status_code=500)
        return path

    @paths_error_handler()
    async def update_path(self, path_id: int, payload: dict) -> dict:
        """Update a learning path and its learning-item ordering.

        Args:
            path_id: Path ID.
            payload: Path updates and typed-item order.

        Returns:
            Updated path payload.

        Raises:
            PathsServiceError: If required fields are missing or the name is duplicate.
        """
        data = self._parse_mutation_payload(payload)
        name = str(data.name or "").strip()
        if not name:
            raise PathsServiceError(detail="missing_name", status_code=400)
        description = str(data.description or "").strip() or None
        items = self._normalize_items_payload(data)

        async with session_scope(self._repo.session):
            if await self._repo.path_name_exists_for_other_id(path_id, name):
                raise PathsServiceError(detail="duplicate_name", status_code=409)
            if await self._repo.has_missing_learning_items(items):
                raise PathsServiceError(detail="invalid_item_refs", status_code=400)
            await self._repo.update_path_with_items(path_id, name, description, items)
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
        async with session_scope(self._repo.session):
            return (await self._repo.delete_path_with_courses(path_id)) > 0

    @staticmethod
    def _path_payload(path: PathRecord) -> dict:
        """Convert a path record into an API payload."""
        return {"id": path.id, "name": path.name, "description": path.description or "", "created_by": path.created_by}

    @staticmethod
    def _course_payload(course: PathLearningItemRecord) -> dict:
        """Convert a course-shaped path item into the legacy course payload."""
        return {
            "id": course.id,
            "title": course.title or "",
            "provider": course.provider or "",
            "category": course.category or "",
            "level": course.level or "",
            "duration_hours": course.duration_hours,
            "url": course.url or "",
        }

    @staticmethod
    def _item_payload(item: PathLearningItemRecord) -> dict:
        """Convert a typed path item into an API payload."""
        return {
            "type": item.item_type,
            "id": item.id,
            "title": item.title or "",
            "description": item.description or "",
            "provider": item.provider or "",
            "category": item.category or "",
            "level": item.level or "",
            "duration_hours": item.duration_hours,
            "url": item.url or "",
            "preview_image_url": item.preview_image_url or "",
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> PathMutationPayload:
        """Parse and validate a path mutation payload."""
        try:
            return PathMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise PathsServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _normalize_items_payload(data: PathMutationPayload) -> list[dict[str, int | str]]:
        """Normalize typed path items, falling back to legacy course_ids when needed."""
        raw_items = list(data.items or [])
        if raw_items:
            sortable: list[tuple[int, int, str, int]] = []
            for idx, raw_item in enumerate(raw_items):
                item_type = str(raw_item.type or "").strip().lower()
                item_id = int(raw_item.id or 0)
                position = int(raw_item.position) if raw_item.position is not None else idx
                sortable.append((position, idx, item_type, item_id))
            normalized: list[dict[str, int | str]] = []
            for out_idx, (_position, _idx, item_type, item_id) in enumerate(sorted(sortable)):
                normalized.append({"type": item_type, "id": item_id, "position": out_idx})
            return normalized
        return [
            {"type": "course", "id": int(course_id), "position": idx} for idx, course_id in enumerate(data.course_ids or [])
        ]
