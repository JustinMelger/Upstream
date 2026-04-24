"""State transition helpers for shared activity feed loads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActivityLoadStart:
    loading: bool


@dataclass(frozen=True)
class ActivityLoadDone:
    loading: bool
    events: list[dict[str, Any]]


def begin_activity_load() -> ActivityLoadStart:
    """Return state values used when activity load starts."""
    return ActivityLoadStart(loading=True)


def finalize_activity_load(*, rows: list[dict[str, Any]] | None) -> ActivityLoadDone:
    """Return state values used when activity load completes."""
    return ActivityLoadDone(loading=False, events=[r for r in list(rows or []) if isinstance(r, dict)])
