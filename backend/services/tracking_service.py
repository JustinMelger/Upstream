from __future__ import annotations

from datetime import datetime, timezone

from pydantic import StrictInt, StrictStr, ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import tracking_error_handler, TrackingServiceError
from backend.database.async_repositories.tracking import TrackingRepository
from backend.database.models import TrackingRecord
from backend.database.tx import session_scope


STATUS_VALUES = {"interested", "in_progress", "completed"}


@dataclass
class TrackingListPayload:
    """Typed service-layer payload for tracking list queries."""

    colleague_id: StrictStr | None = None


@dataclass
class TrackingRecentActivityPayload:
    """Typed service-layer payload for tracking recent activity queries."""

    limit: StrictInt | None = 10


@dataclass
class TrackingMutationPayload:
    """Typed service-layer payload for tracking mutations."""

    colleague_id: StrictStr | None = None
    course_id: StrictInt | None = None
    status: StrictStr | None = None


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
        data = self._parse_list_payload({"colleague_id": colleague_id})
        async with session_scope(self._repo.session):
            rows = await self._repo.list_tracking(data.colleague_id)
        return [self._to_payload(row) for row in rows]

    @tracking_error_handler()
    async def list_recent_activity(self, limit: int = 10) -> list[dict]:
        """List recent tracking activity.

        Args:
            limit: Max number of records.

        Returns:
            Tracking payloads ordered by updated_at desc.
        """
        data = self._parse_recent_activity_payload({"limit": limit})
        safe_limit = max(1, min(data.limit or 10, 100))
        async with session_scope(self._repo.session):
            rows = await self._repo.list_recent_activity(safe_limit)
        return [self._to_payload(row) for row in rows]

    @tracking_error_handler()
    async def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Get tracking stats for a colleague."""
        async with session_scope(self._repo.session):
            return await self._repo.stats_for_colleague(colleague_id)

    @tracking_error_handler()
    async def stats_all(self) -> dict[str, int]:
        """Get tracking stats for all users."""
        async with session_scope(self._repo.session):
            return await self._repo.stats_all()

    @tracking_error_handler()
    async def stats_by_user(self) -> list[dict]:
        """Get tracking stats grouped by user."""
        async with session_scope(self._repo.session):
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
        data = self._parse_mutation_payload(
            {
                "colleague_id": colleague_id,
                "course_id": course_id,
                "status": status,
            }
        )
        username = str(data.colleague_id or "").strip()
        if not username:
            raise TrackingServiceError(detail="invalid_payload", status_code=400)
        course_id_i = data.course_id
        if course_id_i is None:
            raise TrackingServiceError(detail="invalid_payload", status_code=400)
        status_value = str(data.status or "").strip()
        if status_value not in STATUS_VALUES:
            raise TrackingServiceError(detail="invalid_status", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            await self._repo.upsert_tracking(username, course_id_i, status_value, now)
        return {"colleague_id": username, "course_id": str(course_id_i), "status": status_value, "updated_at": now}

    @tracking_error_handler()
    async def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record."""
        data = self._parse_mutation_payload({"colleague_id": colleague_id, "course_id": course_id})
        username = str(data.colleague_id or "").strip()
        if not username:
            raise TrackingServiceError(detail="invalid_payload", status_code=400)
        course_id_i = data.course_id
        if course_id_i is None:
            raise TrackingServiceError(detail="invalid_payload", status_code=400)
        async with session_scope(self._repo.session):
            return await self._repo.remove_tracking(username, course_id_i)

    @staticmethod
    def _to_payload(row: TrackingRecord) -> dict:
        """Convert a tracking record into an API payload."""
        return {
            "colleague_id": row.colleague_id,
            "course_id": str(row.course_id),
            "status": row.status,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def _parse_list_payload(payload: dict) -> TrackingListPayload:
        """Parse and validate a tracking list payload."""
        try:
            return TrackingListPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TrackingServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_recent_activity_payload(payload: dict) -> TrackingRecentActivityPayload:
        """Parse and validate a recent-activity payload."""
        try:
            return TrackingRecentActivityPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TrackingServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> TrackingMutationPayload:
        """Parse and validate a tracking mutation payload."""
        try:
            return TrackingMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TrackingServiceError(detail="invalid_payload", status_code=400) from exc
