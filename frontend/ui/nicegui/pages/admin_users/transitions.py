"""State transition helpers for Admin Users page loads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdminUsersLoadStart:
    loading: bool


@dataclass(frozen=True)
class AdminUsersLoadDone:
    loading: bool
    users: list[dict[str, Any]]


def begin_admin_users_load() -> AdminUsersLoadStart:
    """Return state values used when users load starts."""
    return AdminUsersLoadStart(loading=True)


def finalize_admin_users_load(*, rows: list[dict[str, Any]] | None) -> AdminUsersLoadDone:
    """Return state values used when users load completes."""
    return AdminUsersLoadDone(loading=False, users=[r for r in list(rows or []) if isinstance(r, dict)])
