"""Shared date/time parsing and formatting helpers for the NiceGUI frontend.

These helpers are intentionally small and deterministic, so pages can share
common formatting while keeping UI composition simple.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def parse_iso_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime.

    Notes:
        - Accepts values like `"2026-02-01T12:30:00Z"` by translating the `Z`
          suffix into `+00:00`.
        - If the parsed datetime is naive, it is assumed to be UTC.

    Args:
        value: Any value; it will be coerced to string.

    Returns:
        An aware datetime (UTC where possible), or None when parsing fails.
    """
    s = str(value or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_recent(dt: datetime | None, *, days: int = 7) -> bool:
    """Return True when dt is within the last N days."""
    if dt is None:
        return False
    now = datetime.now(timezone.utc)
    return dt >= (now - timedelta(days=int(days)))


def format_date(ts: str | None, *, fmt: str = "%b %d, %Y") -> str:
    """Format an ISO-8601 timestamp into a short date string."""
    if not ts:
        return ""
    dt = parse_iso_datetime(ts)
    if not dt:
        return str(ts)
    return dt.strftime(fmt)


def format_time(ts: str | None, *, fmt: str = "%b %d, %Y %H:%M") -> str:
    """Format an ISO-8601 timestamp into a short date-time string."""
    if not ts:
        return ""
    dt = parse_iso_datetime(ts)
    if not dt:
        return str(ts)
    return dt.strftime(fmt)
