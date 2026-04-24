"""State transition helpers for shared Home/Profile stats surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SharedStatsLoadStart:
    loading: bool
    meta_text: str


@dataclass(frozen=True)
class SharedStatsLoadDone:
    loading: bool
    meta_text: str


def begin_shared_stats_load() -> SharedStatsLoadStart:
    """Return state values used when overview load starts."""
    return SharedStatsLoadStart(loading=True, meta_text="Loading...")


def finalize_shared_stats_load(*, ok: bool) -> SharedStatsLoadDone:
    """Return state values used when overview load completes."""
    if ok:
        return SharedStatsLoadDone(loading=False, meta_text="Updated")
    return SharedStatsLoadDone(loading=False, meta_text="Failed to load")


def should_render_team_stats(*, is_admin: bool, mode_value: str) -> bool:
    """Whether the team widgets should be shown."""
    return bool(is_admin) and str(mode_value or "mine") == "team"

