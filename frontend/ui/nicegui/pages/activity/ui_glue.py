"""Pure UI helpers for Activity page rendering."""

from __future__ import annotations

from datetime import timezone
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime


def format_when(value: Any) -> str:
    """Format timestamp as UTC activity label."""
    dt = parse_iso_datetime(value)
    if dt is None:
        return str(value or "")
    return dt.astimezone(timezone.utc).strftime("%b %d, %Y %H:%M UTC")


def target_url(*, target_type: str, target_id: int) -> str:
    """Resolve Activity Open-button route for target entity."""
    kind = str(target_type or "")
    if kind == "course":
        return f"/courses?course_id={int(target_id)}"
    if kind == "path":
        return f"/paths?path_id={int(target_id)}"
    if kind == "article":
        return "/articles"
    return "/learning"


def coerce_target_id(value: Any) -> int | None:
    """Safely coerce activity target id to int, returning None when invalid."""
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out if out > 0 else None
