from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.orm_models import Tracking as TrackingModel


class TrackingRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of tracking persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def upsert_tracking(self, colleague_id: str, course_id: int, status: str, updated_at: str | datetime) -> None:
        """Insert or update a tracking record.

        Args:
            colleague_id: Colleague username.
            course_id: Course ID.
            status: Status value.
            updated_at: Timestamp (ISO string).
        """
        stmt = (
            insert(TrackingModel)
            .values(
                colleague_id=colleague_id,
                course_id=course_id,
                status=status,
                updated_at=self._as_datetime(updated_at),
            )
            .on_conflict_do_update(
                index_elements=[TrackingModel.colleague_id, TrackingModel.course_id],
                set_={"status": status, "updated_at": self._as_datetime(updated_at)},
            )
        )
        await self.session.execute(stmt)

    async def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record.

        Args:
            colleague_id: Colleague username.
            course_id: Course ID.

        Returns:
            Number of rows removed.
        """
        result = await self.session.execute(
            delete(TrackingModel)
            .where(func.lower(TrackingModel.colleague_id) == func.lower(colleague_id))
            .where(TrackingModel.course_id == course_id)
        )
        return self._rowcount(result)
