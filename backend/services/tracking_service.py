from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import tracking_error_handler, TrackingServiceError
from backend.database.db import database
from backend.database.interfaces import TrackingRepository
from backend.database.models import TrackingRecord
from backend.database.tracking_repository import SQLiteTrackingRepository


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
    def list_tracking(self, colleague_id: str | None = None) -> list[dict]:
        """List tracking entries, optionally filtered by colleague.

        Args:
            colleague_id: Optional colleague username.

        Returns:
            Tracking payloads.
        """
        return [self._to_payload(row) for row in self._repo.list_tracking(colleague_id)]

    @tracking_error_handler()
    def list_recent_activity(self, limit: int = 10) -> list[dict]:
        """List recent tracking activity.

        Args:
            limit: Max number of records.

        Returns:
            Tracking payloads ordered by updated_at desc.
        """
        return [self._to_payload(row) for row in self._repo.list_recent_activity(limit)]

    @tracking_error_handler()
    def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Get tracking stats for a colleague."""
        return self._repo.stats_for_colleague(colleague_id)

    @tracking_error_handler()
    def stats_all(self) -> dict[str, int]:
        """Get tracking stats for all users."""
        return self._repo.stats_all()

    @tracking_error_handler()
    def stats_by_user(self) -> list[dict]:
        """Get tracking stats grouped by user."""
        return self._repo.stats_by_user()

    @tracking_error_handler()
    def upsert_tracking(self, colleague_id: str, course_id: int, status: str) -> dict:
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
        self._repo.upsert_tracking(colleague_id, course_id, status, now)
        return {"colleague_id": colleague_id, "course_id": str(course_id), "status": status, "updated_at": now}

    @tracking_error_handler()
    def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record."""
        return self._repo.remove_tracking(colleague_id, course_id)

    @staticmethod
    def _to_payload(row: TrackingRecord) -> dict:
        return {
            "colleague_id": row.colleague_id,
            "course_id": str(row.course_id),
            "status": row.status,
            "updated_at": row.updated_at,
        }


tracking_service = TrackingService(SQLiteTrackingRepository(database))
