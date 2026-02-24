from __future__ import annotations

from datetime import datetime


class RepositoryDateTimeCodec:
    """Shared datetime/ISO normalization helpers for async repositories."""

    @staticmethod
    def _as_datetime(value: str | datetime | None) -> datetime | None:
        """Normalize an ISO string/datetime value into datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    @staticmethod
    def _as_iso(value: datetime | str | None) -> str | None:
        """Normalize a datetime/string value into ISO-8601 string."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    @classmethod
    def _as_iso_or_empty(cls, value: datetime | str | None) -> str:
        """Normalize a datetime/string value into ISO string, fallback to empty."""
        return str(cls._as_iso(value) or "")
