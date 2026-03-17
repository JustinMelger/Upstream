"""Shared copy helpers for mixed learning-item and path feeds."""

from __future__ import annotations


def format_count_label(*, count: int, singular: str, plural: str | None = None) -> str:
    """Return a compact count label with basic singular/plural inflection."""
    value = max(0, int(count))
    label = singular if value == 1 else (plural or f"{singular}s")
    return f"{value} {label}"


def format_learning_inventory_text(*, learning_item_count: int, path_count: int, separator: str = " · ") -> str:
    """Return a mixed inventory label for learning items and paths."""
    return separator.join(
        [
            format_count_label(count=learning_item_count, singular="learning item"),
            format_count_label(count=path_count, singular="path"),
        ]
    )


def format_explore_scope_text(*, tab_value: str, course_count: int, video_count: int, article_count: int, path_count: int) -> str:
    """Return the Explore top-bar meta text for the active tab."""
    if tab_value == "courses":
        return format_count_label(count=course_count, singular="course")
    if tab_value == "videos":
        return format_count_label(count=video_count, singular="video")
    if tab_value == "paths":
        return format_count_label(count=path_count, singular="path")
    if tab_value == "articles":
        return format_count_label(count=article_count, singular="article")
    return format_learning_inventory_text(
        learning_item_count=max(0, int(course_count)) + max(0, int(video_count)) + max(0, int(article_count)),
        path_count=path_count,
        separator=" | ",
    )


def activity_empty_description(*, current_tab: str) -> str:
    """Return empty-state copy for the activity feed."""
    if str(current_tab or "").strip().lower() == "team":
        return "When teammates share, recommend, or rate learning items and paths, updates will appear here."
    return "When teammates review or recommend your shared learning items and paths, updates will appear here."


def team_activity_empty_description() -> str:
    """Return empty-state copy for team activity feeds."""
    return "Share a learning item or path to start activity in this feed."
