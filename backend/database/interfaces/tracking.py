from __future__ import annotations

from typing import Protocol

from backend.database.models import TrackingRecord


class TrackingRepository(Protocol):
    def list_tracking(self, colleague_id: str | None) -> list[TrackingRecord]:
        """List tracking entries, optionally filtered by colleague."""

    def list_recent_activity(self, limit: int) -> list[TrackingRecord]:
        """List recent tracking activity."""

    def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Get tracking stats for a colleague."""

    def stats_all(self) -> dict[str, int]:
        """Get tracking stats for all users."""

    def stats_by_user(self) -> list[dict]:
        """Get tracking stats grouped by user."""

    def upsert_tracking(self, colleague_id: str, course_id: int, status: str, updated_at: str) -> None:
        """Insert or update a tracking status."""

    def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record."""
