from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import tracking_error_handler, TrackingServiceError
from backend.database.async_repositories.tracking import TrackingRepository
from backend.database.models import TrackingRecord


STATUS_VALUES = {"interested", "in_progress", "completed"}


class TrackingService:
    """Course tracking service."""

    def __init__(self, repo: TrackingRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for tracking data.
        """
        self._repo = repo

    @tracking_error_handler()
    async def list_tracking(self, colleague_id: str | None = None) -> list[dict]:
        """List tracking entries, optionally filtered by colleague.

        Args:
            colleague_id: Optional colleague username.

        Returns:
            Tracking payloads.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_tracking(colleague_id)
        return [self._to_payload(row) for row in rows]

    @tracking_error_handler()
    async def list_recent_activity(self, limit: int = 10) -> list[dict]:
        """List recent tracking activity.

        Args:
            limit: Max number of records.

        Returns:
            Tracking payloads ordered by updated_at desc.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_recent_activity(limit)
        return [self._to_payload(row) for row in rows]

    @tracking_error_handler()
    async def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Get tracking stats for a colleague."""
        async with self._repo.session.begin():
            return await self._repo.stats_for_colleague(colleague_id)

    @tracking_error_handler()
    async def stats_all(self) -> dict[str, int]:
        """Get tracking stats for all users."""
        async with self._repo.session.begin():
            return await self._repo.stats_all()

    @tracking_error_handler()
    async def stats_by_user(self) -> list[dict]:
        """Get tracking stats grouped by user."""
        async with self._repo.session.begin():
            return await self._repo.stats_by_user()

    @tracking_error_handler()
    async def upsert_tracking(self, colleague_id: str, course_id: int, status: str) -> dict:
        """Insert or update a tracking status.

        Args:
            colleague_id: Colleague username.
            course_id: Course ID.
            status: Tracking status.

        Returns:
            Tracking payload.

        Raises:
            TrackingServiceError: If status is invalid.
        """
        if status not in STATUS_VALUES:
            raise TrackingServiceError(detail="invalid_status", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with self._repo.session.begin():
            await self._repo.upsert_tracking(colleague_id, course_id, status, now)
        return {"colleague_id": colleague_id, "course_id": str(course_id), "status": status, "updated_at": now}

    @tracking_error_handler()
    async def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record."""
        async with self._repo.session.begin():
            return await self._repo.remove_tracking(colleague_id, course_id)

    @staticmethod
    def _to_payload(row: TrackingRecord) -> dict:
        """Convert a tracking record into an API payload."""
        return {
            "colleague_id": row.colleague_id,
            "course_id": str(row.course_id),
            "status": row.status,
            "updated_at": row.updated_at,
        }
