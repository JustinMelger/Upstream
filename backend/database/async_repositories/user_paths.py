from __future__ import annotations

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import SelectedPathRecord
from backend.database.orm_models import Path as PathModel, UserPath as UserPathModel


class UserPathsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of user path selection persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def path_exists(self, path_id: int) -> bool:
        """Return whether a path id exists."""
        result = await self.session.execute(select(PathModel.id).where(PathModel.id == int(path_id)).limit(1))
        return result.scalar_one_or_none() is not None

    async def add_user_path(self, colleague_id: str, path_id: int, now: str | datetime) -> int:
        """Add a path selection for a user.

        Args:
            colleague_id: Colleague username.
            path_id: Path ID.
            now: Timestamp (ISO string).

        Returns:
            Number of rows inserted (1 on success).
        """
        stmt = (
            insert(UserPathModel)
            .values(
                colleague_id=colleague_id,
                path_id=path_id,
                created_at=self._as_datetime(now),
                updated_at=self._as_datetime(now),
                status="interested",
            )
            .on_conflict_do_update(
                index_elements=[UserPathModel.colleague_id, UserPathModel.path_id],
                set_={
                    "updated_at": self._as_datetime(now),
                    "status": case(
                        (UserPathModel.status.is_(None), "interested"),
                        else_=UserPathModel.status,
                    ),
                },
            )
        )
        await self.session.execute(stmt)
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

    async def update_user_path_status(self, colleague_id: str, path_id: int, status: str, now: str | datetime) -> int:
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
            .values(status=status, updated_at=self._as_datetime(now))
        )
        return int(result.rowcount or 0)
