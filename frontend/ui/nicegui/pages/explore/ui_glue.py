"""UI glue helpers for Explore page controls and labels."""

from __future__ import annotations

from typing import Any


TAB_OPTIONS = {"all": "All", "courses": "Courses", "paths": "Paths", "articles": "Articles"}
SORT_OPTIONS = {
    "": "Recommended",
    "newest": "Newest",
    "title_az": "Title A-Z",
}


def normalize_tab(raw: Any) -> str:
    """Normalize tab query/control value to allowed options."""
    value = str(raw or "").strip().lower()
    return value if value in TAB_OPTIONS else "all"


def normalize_sort(raw: Any) -> str:
    """Normalize sort control value to allowed options."""
    value = str(raw or "").strip().lower()
    return value if value in SORT_OPTIONS else ""


def compute_explore_meta_text(*, tab_value: str, course_count: int, path_count: int, article_count: int) -> str:
    """Build topbar meta text for current Explore scope."""
    if tab_value == "courses":
        return f"{int(course_count)} courses"
    if tab_value == "paths":
        return f"{int(path_count)} paths"
    if tab_value == "articles":
        return f"{int(article_count)} articles"
    return f"{int(course_count)} courses | {int(path_count)} paths | {int(article_count)} articles"
