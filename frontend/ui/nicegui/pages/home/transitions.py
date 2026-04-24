"""State transition helpers for shared Home/Profile stats surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HomeLoadStart:
    loading: bool
    meta_text: str


@dataclass(frozen=True)
class HomeLoadDone:
    loading: bool
    meta_text: str


def begin_home_load() -> HomeLoadStart:
    """Return state values used when overview load starts."""
    return HomeLoadStart(loading=True, meta_text="Loading...")


def finalize_home_load(*, ok: bool) -> HomeLoadDone:
    """Return state values used when overview load completes."""
    if ok:
        return HomeLoadDone(loading=False, meta_text="Updated")
    return HomeLoadDone(loading=False, meta_text="Failed to load")


def should_render_team_section(*, is_admin: bool, mode_value: str) -> bool:
    """Whether the team widgets should be shown."""
    return bool(is_admin) and str(mode_value or "mine") == "team"
