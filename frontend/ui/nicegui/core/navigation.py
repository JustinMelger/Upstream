"""Shared URL/deep-link builders for frontend page navigation."""

from __future__ import annotations


def build_courses_deep_link(*, course_id: int, view: str = "full", tab: str = "tracked") -> str:
    """Build stable courses page deep-link URL."""
    return f"/courses?tab={str(tab or 'tracked')}&course_id={int(course_id)}&view={str(view or 'full')}"


def build_paths_deep_link(*, path_id: int, view: str = "full", tab: str = "selected") -> str:
    """Build stable paths page deep-link URL."""
    return f"/paths?tab={str(tab or 'selected')}&path_id={int(path_id)}&view={str(view or 'full')}"


def build_learning_tab_link(*, tab: str) -> str:
    """Build stable home-tab URL."""
    return f"/home?tab={str(tab or 'learning')}"


def build_activity_tab_link(*, tab: str) -> str:
    """Build stable teams-tab URL."""
    return f"/teams?tab={str(tab or 'inbox')}"


def build_activity_target_link(*, target_type: str, target_id: int) -> str:
    """Resolve Activity Open-button route for target entity."""
    kind = str(target_type or "")
    if kind == "course":
        return f"/courses?course_id={int(target_id)}"
    if kind == "path":
        return f"/paths?path_id={int(target_id)}"
    if kind == "article":
        return "/articles"
    return "/home"
