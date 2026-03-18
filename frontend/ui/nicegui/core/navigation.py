"""Shared URL/deep-link builders for frontend page navigation."""

from __future__ import annotations


def build_courses_deep_link(*, course_id: int, view: str = "full", tab: str = "tracked") -> str:
    """Build stable Explore course-detail deep-link URL."""
    _ = tab
    mode_qs = "?view=reviews" if str(view or "").strip().lower() == "reviews" else ""
    return f"/explore/courses/{int(course_id)}{mode_qs}"


def build_paths_deep_link(*, path_id: int, view: str = "full", tab: str = "selected") -> str:
    """Build stable Explore path-detail deep-link URL."""
    _ = tab
    mode_qs = "?view=reviews" if str(view or "").strip().lower() == "reviews" else ""
    return f"/explore/paths/{int(path_id)}{mode_qs}"


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
        return f"/explore/courses/{int(target_id)}"
    if kind == "video":
        return f"/explore/videos/{int(target_id)}"
    if kind == "path":
        return f"/explore/paths/{int(target_id)}"
    if kind == "article":
        return "/explore?tab=articles"
    return "/home"
