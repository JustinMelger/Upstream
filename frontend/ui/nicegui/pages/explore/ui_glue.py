"""UI glue helpers for Explore page controls and labels."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags


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


def apply_tab_scope(
    *,
    tab_value: str,
    shown_courses: list[dict[str, Any]],
    shown_paths: list[dict[str, Any]],
    shown_articles: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply tab filter to the three Explore result buckets."""
    if tab_value == "courses":
        return shown_courses, [], []
    if tab_value == "paths":
        return [], shown_paths, []
    if tab_value == "articles":
        return [], [], shown_articles
    return shown_courses, shown_paths, shown_articles


def build_explore_filter_options(
    *,
    courses: list[dict[str, Any]],
    articles: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    """Build provider/category/tag/author options from loaded Explore datasets."""
    provider_options = {"": "Any provider"}
    category_options = {"": "Any category"}
    for row in list(courses or []):
        provider = str(row.get("provider") or "").strip()
        category = str(row.get("category") or "").strip()
        if provider and provider not in provider_options:
            provider_options[provider] = provider
        if category and category not in category_options:
            category_options[category] = category

    tag_options = {"": "Any tag"}
    author_options = {"": "Anyone"}
    for row in list(articles or []):
        author = str(row.get("created_by") or "").strip()
        if author and author not in author_options:
            author_options[author] = author
        for tag in parse_tags(str(row.get("tags") or "")):
            if tag and tag not in tag_options:
                tag_options[tag] = tag

    return provider_options, category_options, tag_options, author_options


def clear_explore_filter_controls(*, controls: Any) -> None:
    """Reset all Explore drawer filters to empty values."""
    for control in [
        controls.provider_filter,
        controls.category_filter,
        controls.tag_filter,
        controls.author_filter,
    ]:
        control.value = ""
        control.update()


def apply_explore_filter_options(
    *,
    controls: Any,
    courses: list[dict[str, Any]],
    articles: list[dict[str, Any]],
) -> None:
    """Apply computed facet options to Explore drawer controls."""
    provider_options, category_options, tag_options, author_options = build_explore_filter_options(
        courses=courses,
        articles=articles,
    )
    controls.provider_filter.options = provider_options
    controls.provider_filter.update()
    controls.category_filter.options = category_options
    controls.category_filter.update()
    controls.tag_filter.options = tag_options
    controls.tag_filter.update()
    controls.author_filter.options = author_options
    controls.author_filter.update()
