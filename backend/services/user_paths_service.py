from __future__ import annotations

from datetime import datetime, timezone

from pydantic import StrictInt, StrictStr, ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import user_paths_error_handler, UserPathsServiceError
from backend.database.async_repositories.user_paths import UserPathsRepository
from backend.database.tx import session_scope


STATUS_VALUES = {"interested", "in_progress", "completed"}


@dataclass
class UserPathMutationPayload:
    """Typed service-layer payload for user path mutations."""

    colleague_id: StrictStr | None = None
    path_id: StrictInt | None = None
    status: StrictStr | None = None


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
        data = self._parse_mutation_payload({"colleague_id": colleague_id, "path_id": path_id})
        username = str(data.colleague_id or "").strip()
        if not username:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        path_id_i = data.path_id
        if path_id_i is None:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            if not await self._repo.path_exists(path_id_i):
                raise UserPathsServiceError(detail="not_found", status_code=404)
            await self._repo.add_user_path(username, path_id_i, now)
        return {"colleague_id": username, "path_id": str(path_id_i), "created_at": now}

    @user_paths_error_handler()
    async def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a path from a user's selections.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Number of rows removed.
        """
        data = self._parse_mutation_payload({"colleague_id": colleague_id, "path_id": path_id})
        username = str(data.colleague_id or "").strip()
        if not username:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        path_id_i = data.path_id
        if path_id_i is None:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        async with session_scope(self._repo.session):
            return await self._repo.remove_user_path(username, path_id_i)

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
        data = self._parse_mutation_payload(
            {
                "colleague_id": colleague_id,
                "path_id": path_id,
                "status": status,
            }
        )
        username = str(data.colleague_id or "").strip()
        if not username:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        path_id_i = data.path_id
        if path_id_i is None:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400)
        status_value = str(data.status or "").strip()
        if status_value not in STATUS_VALUES:
            raise UserPathsServiceError(detail="invalid_status", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            return await self._repo.update_user_path_status(username, path_id_i, status_value, now)

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> UserPathMutationPayload:
        """Parse and validate a user path mutation payload."""
        try:
            return UserPathMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise UserPathsServiceError(detail="invalid_payload", status_code=400) from exc
