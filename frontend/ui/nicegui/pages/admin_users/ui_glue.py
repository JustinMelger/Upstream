"""Pure helper functions for Admin Users page UI."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.datetime_utils import format_time


_format_time = format_time


def _user_row(u: dict[str, Any]) -> dict[str, Any]:
    """Map a backend user payload into a table row."""
    return {
        "username": u.get("username") or "",
        "role": u.get("role") or "",
        "created_at": _format_time(str(u.get("created_at") or "")),
        "updated_at": _format_time(str(u.get("updated_at") or "")),
        "last_login_at": _format_time(str(u.get("last_login_at") or "")),
        "disabled": "Yes" if u.get("disabled") else "No",
    }


def _filter_users(users: list[dict[str, Any]] | None, needle: str) -> list[dict[str, Any]]:
    """Filter users by substring match on username or role."""
    all_users = list(users or [])
    if not needle:
        return all_users
    n = needle.strip().lower()
    if not n:
        return all_users
    return [u for u in all_users if n in str(u.get("username") or "").lower() or n in str(u.get("role") or "").lower()]
