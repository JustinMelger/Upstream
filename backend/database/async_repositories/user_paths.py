from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import SelectedPathRecord
from backend.database.orm_models import Path as PathModel, UserPath as UserPathModel


class UserPathsRepository:
    """Async SQLAlchemy implementation of user path selection persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def add_user_path(self, colleague_id: str, path_id: int, now: str) -> int:
        """Add a path selection for a user.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.
            now: Timestamp (ISO string).

        Returns:
            Number of rows inserted (1 on success).
        """
        self.session.add(UserPathModel(colleague_id=colleague_id, path_id=path_id, created_at=now))
        await self.session.flush()
        return 1

    async def list_user_paths(self, colleague_id: str) -> list[SelectedPathRecord]:
        """List selected paths for a colleague.

        Args:
            colleague_id: Colleague username.

        Returns:
            List of selected path records.
        """
        result = await self.session.execute(
            select(PathModel.id, PathModel.name, PathModel.description, UserPathModel.status)
            .join(UserPathModel, UserPathModel.path_id == PathModel.id)
            .where(func.lower(UserPathModel.colleague_id) == func.lower(colleague_id))
            .order_by(PathModel.name.asc())
        )
        rows = result.all()
        return [SelectedPathRecord(id=row.id, name=row.name, description=row.description, status=row.status) for row in rows]

    async def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a selected path for a colleague.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.

        Returns:
            Number of rows removed.
        """
        result = await self.session.execute(
            delete(UserPathModel)
            .where(func.lower(UserPathModel.colleague_id) == func.lower(colleague_id))
            .where(UserPathModel.path_id == path_id)
        )
        return int(result.rowcount or 0)

    async def update_user_path_status(self, colleague_id: str, path_id: int, status: str, now: str) -> int:
        """Update status for a selected path.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.
            status: Status value.
            now: Timestamp (ISO string).

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(UserPathModel)
            .where(func.lower(UserPathModel.colleague_id) == func.lower(colleague_id))
            .where(UserPathModel.path_id == path_id)
            .values(status=status, updated_at=now)
        )
        return int(result.rowcount or 0)
