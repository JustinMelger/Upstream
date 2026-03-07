"""Result-section rendering helpers for Explore page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.explore.list_items import render_article_item, render_course_item, render_path_item


_DEFAULT_COURSE_CAP = 8
_DEFAULT_PATH_CAP = 6
_DEFAULT_ARTICLE_CAP = 8
_CURATED_PATH_COUNT = 3
_CURATED_ARTICLE_COUNT = 4


@dataclass(frozen=True, slots=True)
class ExploreSectionsDeps:
    """Dependencies for rendering mixed Explore sections."""

    state: Any
    username: str
    is_admin: bool
    show_all_categories: bool
    course_actions_builder: Callable[[dict[str, Any], int, str], Any]
    on_set_tracking: Callable[[int, str], Awaitable[None]]
    on_clear_tracking: Callable[[int], Awaitable[None]]
    on_toggle_path_selection: Callable[[int], Awaitable[None]]
    open_path_details_dialog: Callable[[dict[str, Any], Any], None]
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]]
    course_category: str
    on_set_course_category: Callable[[str], None]
    courses_visible_limit: int
    on_show_more_courses: Callable[[], None]


def render_explore_course_spotlight(
    *,
    shown_courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    course_actions_builder: Callable[[dict[str, Any], int, str], Any],
    on_track: Callable[[int, str], Awaitable[None]],
) -> None:
    """Render compact Explore spotlight strip."""
    if not shown_courses:
        return
    from frontend.ui.nicegui.pages.explore.sections import render_explore_spotlight_strip

    spotlight = shown_courses[0]
    spotlight_id = int(spotlight.get("id") or 0)
    spotlight_tracked = isinstance(tracking_by_course_id.get(spotlight_id), dict)

    async def _spotlight_primary() -> None:
        if spotlight_tracked:
            await course_actions_builder(
                spotlight,
                spotlight_id,
                str(spotlight.get("url") or "").strip(),
            ).on_view()
            return
        await on_track(spotlight_id, "interested")

    render_explore_spotlight_strip(
        title=str(spotlight.get("title") or ""),
        description=str(spotlight.get("description") or ""),
        shared_by=str(spotlight.get("created_by") or ""),
        on_primary=_spotlight_primary,
    )


def render_explore_sections(
    *,
    shown_courses: list[dict[str, Any]],
    shown_paths: list[dict[str, Any]],
    shown_articles: list[dict[str, Any]],
    deps: ExploreSectionsDeps,
) -> None:
    """Render the mixed Explore sections for courses/paths/articles."""
    course_cap = 16 if deps.show_all_categories else _DEFAULT_COURSE_CAP
    path_cap = 12 if deps.show_all_categories else _DEFAULT_PATH_CAP
    article_cap = 16 if deps.show_all_categories else _DEFAULT_ARTICLE_CAP

    visible_courses = shown_courses[:course_cap]
    visible_paths = shown_paths[:path_cap]
    visible_articles = shown_articles[:article_cap]

    if visible_courses:
        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.column().classes("w-full gap-2 lp-courses-section"):
                ui.label("Recommended for you").classes("lp-courses-section-title")
                ui.label("Start here based on your activity and selected scope.").classes("lp-courses-section-subtitle")
            render_explore_course_spotlight(
                shown_courses=visible_courses,
                tracking_by_course_id=deps.state.tracking_by_course_id,
                course_actions_builder=deps.course_actions_builder,
                on_track=deps.on_set_tracking,
            )

    if visible_paths:
        shown_paths_rows = (
            visible_paths[:_CURATED_PATH_COUNT] if not deps.show_all_categories else visible_paths[:_DEFAULT_PATH_CAP]
        )
        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-1"):
                    ui.label("Learning paths").classes("lp-courses-section-title")
                    ui.label("Structured tracks to guide your next steps.").classes("lp-courses-section-subtitle")
                ui.link("View all paths", "/explore?tab=paths").classes("text-sm")
            with ui.element("div").classes("lp-courses-grid lp-explore-path-grid"):
                for row in shown_paths_rows:
                    render_path_item(
                        path=row,
                        item_classes="lp-courses-grid-item",
                        state=deps.state,
                        username=deps.username,
                        is_admin=deps.is_admin,
                        on_toggle_path_selection=deps.on_toggle_path_selection,
                        open_path_details_dialog=deps.open_path_details_dialog,
                    )

    if visible_courses:
        categories = _course_categories(courses=visible_courses)
        selected_category = str(deps.course_category or "all")
        filtered_courses = _filter_courses_by_category(
            courses=visible_courses,
            category_value=selected_category,
        )
        limit = max(1, int(deps.courses_visible_limit or _DEFAULT_COURSE_CAP))
        shown_course_rows = filtered_courses[:limit]

        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-1"):
                    ui.label("Courses").classes("lp-courses-section-title")
                    ui.label("Browse all courses.").classes("lp-courses-section-subtitle")
                ui.link("View all courses", "/explore?tab=courses").classes("text-sm")
            with ui.row().classes("items-center gap-2 w-full flex-wrap"):
                all_props = "dense" if selected_category.lower() == "all" else "outline dense"
                all_btn = ui.button("All", on_click=lambda: deps.on_set_course_category("all")).props(all_props)
                all_btn.classes("lp-explore-category-btn")
                if selected_category.lower() == "all":
                    all_btn.classes("lp-explore-category-btn--active")
                for category in categories:
                    btn_props = "dense" if selected_category.lower() == category.lower() else "outline dense"
                    btn = ui.button(
                        category,
                        on_click=lambda _category=category: deps.on_set_course_category(_category),
                    ).props(btn_props)
                    btn.classes("lp-explore-category-btn")
                    if selected_category.lower() == category.lower():
                        btn.classes("lp-explore-category-btn--active")
            with ui.element("div").classes("lp-courses-grid lp-explore-course-grid"):
                for row in shown_course_rows:
                    render_course_item(
                        course=row,
                        item_classes="lp-courses-grid-item",
                        state=deps.state,
                        username=deps.username,
                        is_admin=deps.is_admin,
                        course_actions_builder=deps.course_actions_builder,
                        on_set_tracking=deps.on_set_tracking,
                        on_clear_tracking=deps.on_clear_tracking,
                    )
            if len(filtered_courses) > len(shown_course_rows):
                with ui.row().classes("items-center justify-center w-full"):
                    ui.button("Show more courses", on_click=deps.on_show_more_courses).props("outline dense")

    if visible_articles:
        shown_articles_rows = (
            visible_articles[:_CURATED_ARTICLE_COUNT]
            if not deps.show_all_categories
            else visible_articles[:_DEFAULT_ARTICLE_CAP]
        )
        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.column().classes("w-full gap-2 lp-courses-section"):
                ui.label("Articles for quick context").classes("lp-courses-section-title")
                ui.label("Short reads to sharpen decisions before you commit to a course or path.").classes(
                    "lp-courses-section-subtitle"
                )
                with ui.element("div").classes("lp-courses-grid lp-explore-article-grid"):
                    for row in shown_articles_rows:
                        render_article_item(
                            article=row,
                            item_classes="lp-courses-grid-item",
                            state=deps.state,
                            open_article_details=deps.open_article_details,
                        )
            if not deps.show_all_categories and len(visible_articles) > len(shown_articles_rows):
                with ui.row().classes("items-center justify-end w-full"):
                    ui.link("View all articles", "/explore?tab=articles").classes("text-sm")


def _course_categories(*, courses: list[dict[str, Any]]) -> list[str]:
    """Return top categories ranked by frequency."""
    counts: dict[str, int] = {}
    for row in courses:
        name = str(row.get("category") or "").strip() or "General"
        counts[name] = int(counts.get(name) or 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [name for name, _count in ranked[:6]]


def _filter_courses_by_category(*, courses: list[dict[str, Any]], category_value: str) -> list[dict[str, Any]]:
    """Filter course rows by selected category value."""
    selected = str(category_value or "all").strip().lower()
    if selected in {"", "all"}:
        return list(courses or [])
    return [row for row in courses if (str(row.get("category") or "").strip() or "General").lower() == selected]


def render_explore_empty_state(
    *,
    loaded_once: bool,
    on_refresh: Callable[[], Any],
    on_reset_filters: Callable[[], Any],
) -> None:
    """Render the Explore empty/error state block."""
    with ui.column().classes("w-full gap-2 lp-courses-section"):
        if not loaded_once:
            ui.label("Discovery feed unavailable").classes("lp-courses-section-title")
            ui.label("Explore could not load right now. Refresh to retry.").classes("lp-courses-section-subtitle")
            ui.button("Refresh explore", on_click=on_refresh).props("outline")
            return
        ui.label("No matches in Explore").classes("lp-courses-section-title")
        ui.label("Reset filters to widen your discovery results.").classes("lp-courses-section-subtitle")
        ui.button("Reset filters", on_click=on_reset_filters).props("outline")
