from __future__ import annotations

from datetime import datetime, timezone

from backend.database.db import database
from backend.database.interfaces import UserPathsRepository
from backend.database.models import SelectedPathRecord
from backend.database.user_paths_repository import SQLiteUserPathsRepository


STATUS_VALUES = {"interested", "in_progress", "completed"}


class UserPathsService:
    """User learning path selection service."""

    def __init__(self, repo: UserPathsRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for user path selections.
        """
        self._repo = repo

    def add_user_path(self, colleague_id: str, path_id: int) -> dict:
        """Add a path to a user's selections.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Selection record payload.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._repo.add_user_path(colleague_id, path_id, now)
        return {"colleague_id": colleague_id, "path_id": str(path_id), "created_at": now}

    def list_user_paths(self, colleague_id: str) -> list[dict]:
        """List paths selected by a colleague.

        Args:
            colleague_id: Colleague username.

        Returns:
            Selected path payloads.
        """
        return [self._to_payload(path) for path in self._repo.list_user_paths(colleague_id)]

    def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a path from a user's selections.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Number of rows removed.
        """
        return self._repo.remove_user_path(colleague_id, path_id)

    def update_user_path_status(self, colleague_id: str, path_id: int, status: str) -> int:
        """Update a user's status for a selected path.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.
            status: Status value.

        Returns:
            Number of rows updated.

        Raises:
            ValueError: If status is invalid.
        """
        if status not in STATUS_VALUES:
            raise ValueError("invalid_status")
        now = datetime.now(timezone.utc).isoformat()
        return self._repo.update_user_path_status(colleague_id, path_id, status, now)

    @staticmethod
    def _to_payload(path: SelectedPathRecord) -> dict:
        return {
            "id": path.id,
            "name": path.name,
            "description": path.description or "",
            "status": path.status or "",
        }


user_paths_service = UserPathsService(SQLiteUserPathsRepository(database))


def get_user_paths_service() -> UserPathsService:
    """Provide the UserPathsService dependency.

    Returns:
        UserPathsService: Shared user paths service instance.
    """
    return user_paths_service
