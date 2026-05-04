from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import TrackingRecord
from backend.database.orm_models import Tracking as TrackingModel


STATUS_VALUES = ("interested", "in_progress", "completed")


class TrackingRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of tracking persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_tracking(self, colleague_id: str | None) -> list[TrackingRecord]:
        """List tracking records, optionally filtered by colleague.

        Args:
            colleague_id: Optional colleague username.

        Returns:
            Tracking records.
        """
        stmt = select(TrackingModel).order_by(TrackingModel.updated_at.desc())
        if colleague_id:
            stmt = stmt.where(func.lower(TrackingModel.colleague_id) == func.lower(colleague_id))
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            TrackingRecord(
                colleague_id=row.colleague_id,
                course_id=row.course_id,
                status=row.status,
                updated_at=self._as_iso_or_empty(row.updated_at),
            )
            for row in rows
        ]

    async def list_recent_activity(self, limit: int) -> list[TrackingRecord]:
        """List recent tracking activity.

        Args:
            limit: Maximum number of records.

        Returns:
            Tracking records ordered by updated_at desc.
        """
        result = await self.session.execute(select(TrackingModel).order_by(TrackingModel.updated_at.desc()).limit(limit))
        rows = result.scalars().all()
        return [
            TrackingRecord(
                colleague_id=row.colleague_id,
                course_id=row.course_id,
                status=row.status,
                updated_at=self._as_iso_or_empty(row.updated_at),
            )
            for row in rows
        ]

    async def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Compute status counts for a colleague.

        Args:
            colleague_id: Colleague username.

        Returns:
            Mapping of status -> count.
        """
        result = await self.session.execute(
            select(TrackingModel.status, func.count().label("count"))
            .where(func.lower(TrackingModel.colleague_id) == func.lower(colleague_id))
            .group_by(TrackingModel.status)
        )
        counts = {status: 0 for status in STATUS_VALUES}
        for status, count in result.all():
            counts[str(status)] = int(count)
        return counts

    async def stats_all(self) -> dict[str, int]:
        """Compute status counts across all colleagues.

        Returns:
            Mapping of status -> count.
        """
        result = await self.session.execute(
            select(TrackingModel.status, func.count().label("count")).group_by(TrackingModel.status)
        )
        counts = {status: 0 for status in STATUS_VALUES}
        for status, count in result.all():
            counts[str(status)] = int(count)
        return counts

    async def stats_for_users(self, colleague_ids: list[str]) -> dict[str, int]:
        """Compute status counts across a set of colleagues."""
        normalized_ids = sorted(
            {str(user_id or "").strip().lower() for user_id in list(colleague_ids or []) if str(user_id or "").strip()}
        )
        counts = {status: 0 for status in STATUS_VALUES}
        if not normalized_ids:
            return counts
        result = await self.session.execute(
            select(TrackingModel.status, func.count().label("count"))
            .where(func.lower(TrackingModel.colleague_id).in_(normalized_ids))
            .group_by(TrackingModel.status)
        )
        for status, count in result.all():
            counts[str(status)] = int(count)
        return counts

    async def stats_by_user(self) -> list[dict]:
        """Compute status counts grouped by colleague.

        Returns:
            List of dict payloads with counts per status.
        """
        result = await self.session.execute(
            select(
                TrackingModel.colleague_id,
                func.sum(case((TrackingModel.status == "interested", 1), else_=0)).label("interested"),
                func.sum(case((TrackingModel.status == "in_progress", 1), else_=0)).label("in_progress"),
                func.sum(case((TrackingModel.status == "completed", 1), else_=0)).label("completed"),
            ).group_by(TrackingModel.colleague_id)
        )
        return [
            {
                "colleague_id": row.colleague_id,
                "interested": int(row.interested or 0),
                "in_progress": int(row.in_progress or 0),
                "completed": int(row.completed or 0),
            }
            for row in result.all()
        ]

    async def stats_by_users(self, colleague_ids: list[str]) -> list[dict]:
        """Compute status counts grouped by colleague for a selected user set."""
        normalized_ids = sorted(
            {str(user_id or "").strip().lower() for user_id in list(colleague_ids or []) if str(user_id or "").strip()}
        )
        if not normalized_ids:
            return []
        result = await self.session.execute(
            select(
                TrackingModel.colleague_id,
                func.sum(case((TrackingModel.status == "interested", 1), else_=0)).label("interested"),
                func.sum(case((TrackingModel.status == "in_progress", 1), else_=0)).label("in_progress"),
                func.sum(case((TrackingModel.status == "completed", 1), else_=0)).label("completed"),
            )
            .where(func.lower(TrackingModel.colleague_id).in_(normalized_ids))
            .group_by(TrackingModel.colleague_id)
            .order_by(func.lower(TrackingModel.colleague_id).asc())
        )
        return [
            {
                "colleague_id": row.colleague_id,
                "interested": int(row.interested or 0),
                "in_progress": int(row.in_progress or 0),
                "completed": int(row.completed or 0),
            }
            for row in result.all()
        ]

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
