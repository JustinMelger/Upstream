from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import user_paths_error_handler, UserPathsServiceError
from backend.database.async_repositories.user_paths import UserPathsRepository
from backend.database.models import SelectedPathRecord


STATUS_VALUES = {"interested", "in_progress", "completed"}


class UserPathsService:
    """User learning path selection service."""

    def __init__(self, repo: UserPathsRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for user path selections.
        """
        self._repo = repo

    @user_paths_error_handler()
    async def add_user_path(self, colleague_id: str, path_id: int) -> dict:
        """Add a path to a user's selections.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Selection record payload.
        """
        now = datetime.now(timezone.utc).isoformat()
        async with self._repo.session.begin():
            await self._repo.add_user_path(colleague_id, path_id, now)
        return {"colleague_id": colleague_id, "path_id": str(path_id), "created_at": now}

    @user_paths_error_handler()
    async def list_user_paths(self, colleague_id: str) -> list[dict]:
        """List paths selected by a colleague.

        Args:
            colleague_id: Colleague username.

        Returns:
            Selected path payloads.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_user_paths(colleague_id)
        return [self._to_payload(path) for path in rows]

    @user_paths_error_handler()
    async def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a path from a user's selections.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Number of rows removed.
        """
        async with self._repo.session.begin():
            return await self._repo.remove_user_path(colleague_id, path_id)

    @user_paths_error_handler()
    async def update_user_path_status(self, colleague_id: str, path_id: int, status: str) -> int:
        """Update a user's status for a selected path.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.
            status: Status value.

        Returns:
            Number of rows updated.

        Raises:
            UserPathsServiceError: If status is invalid.
        """
        if status not in STATUS_VALUES:
            raise UserPathsServiceError(detail="invalid_status", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with self._repo.session.begin():
            return await self._repo.update_user_path_status(colleague_id, path_id, status, now)

    @staticmethod
    def _to_payload(path: SelectedPathRecord) -> dict:
        """Convert a selected path record into an API payload."""
        return {
            "id": path.id,
            "name": path.name,
            "description": path.description or "",
            "status": path.status or "",
        }
