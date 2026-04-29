"""Result-section rendering helpers for Explore page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.explore.list_items import (
    render_article_item,
    render_course_item,
    render_path_item,
    render_video_item,
)
from frontend.ui.nicegui.pages.explore.view_model import ExploreLearningItemEntry


_DEFAULT_COURSE_CAP = 6
_DEFAULT_PATH_CAP = 6
_DEFAULT_LEARNING_ITEM_CAP = 8
_CURATED_PATH_COUNT = 3


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
    open_path: Callable[[int], None]
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]]
    learning_items_visible_limit: int
    on_show_more_learning_items: Callable[[], None]


def render_explore_sections(
    *,
    shown_courses: list[dict[str, Any]],
    shown_paths: list[dict[str, Any]],
    shown_learning_items: list[ExploreLearningItemEntry],
    deps: ExploreSectionsDeps,
) -> None:
    """Render the Explore browse sections with rows for results and cards for paths."""
    course_cap = 16 if deps.show_all_categories else _DEFAULT_COURSE_CAP
    path_cap = 12 if deps.show_all_categories else _DEFAULT_PATH_CAP
    visible_courses = shown_courses[:course_cap]
    visible_paths = shown_paths[:path_cap]
    visible_learning_items = list(shown_learning_items or [])

    if visible_courses:
        featured_courses = visible_courses[:1]
        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-end justify-between w-full lp-explore-section-head"):
                with ui.column().classes("gap-1"):
                    ui.label("Featured courses").classes("lp-courses-section-title")
                    ui.label("Highlighted courses from the current scope.").classes("lp-courses-section-subtitle")
            with ui.column().classes("w-full gap-3 lp-explore-results-list"):
                for row in featured_courses:
                    render_course_item(
                        course=row,
                        item_classes="lp-explore-results-list-item",
                        state=deps.state,
                        username=deps.username,
                        is_admin=deps.is_admin,
                        course_actions_builder=deps.course_actions_builder,
                        item_type="course",
                        on_set_tracking=deps.on_set_tracking,
                        on_clear_tracking=deps.on_clear_tracking,
                    )

    if visible_paths:
        shown_paths_rows = (
            visible_paths[:_CURATED_PATH_COUNT] if not deps.show_all_categories else visible_paths[:_DEFAULT_PATH_CAP]
        )
        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-end justify-between w-full lp-explore-section-head"):
                with ui.column().classes("gap-1"):
                    ui.label("Learning paths").classes("lp-courses-section-title")
                    ui.label("Structured tracks to guide your next steps.").classes("lp-courses-section-subtitle")
                ui.link("View all paths", "/explore?tab=paths").classes("text-sm")
            path_grid_class = "lp-explore-path-grid"
            if len(shown_paths_rows) == 1:
                path_grid_class += " lp-explore-path-grid--single"
            elif len(shown_paths_rows) == 2:
                path_grid_class += " lp-explore-path-grid--pair"
            with ui.element("div").classes(path_grid_class):
                for row in shown_paths_rows:
                    render_path_item(
                        path=row,
                        item_classes="lp-courses-grid-item",
                        state=deps.state,
                        username=deps.username,
                        is_admin=deps.is_admin,
                        on_toggle_path_selection=deps.on_toggle_path_selection,
                        open_path=deps.open_path,
                    )

    if visible_learning_items:
        limit = max(1, int(deps.learning_items_visible_limit or _DEFAULT_LEARNING_ITEM_CAP))
        shown_learning_item_rows = visible_learning_items[:limit]

        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-end justify-between w-full lp-explore-section-head"):
                with ui.column().classes("gap-1"):
                    ui.label("All learning items").classes("lp-courses-section-title")
                    ui.label("Courses, videos, and articles across the current scope.").classes("lp-courses-section-subtitle")
            with ui.column().classes("w-full gap-3 lp-explore-results-list"):
                for item in shown_learning_item_rows:
                    row = dict(item.row or {})
                    item_type = str(item.learning_item_type or "").strip().lower()
                    if item_type == "article":
                        render_article_item(
                            article=row,
                            item_classes="lp-explore-results-list-item",
                            state=deps.state,
                            open_article_details=deps.open_article_details,
                        )
                        continue
                    if item_type == "video":
                        render_video_item(
                            video=row,
                            item_classes="lp-explore-results-list-item",
                            state=deps.state,
                        )
                        continue
                    render_course_item(
                        course=row,
                        item_classes="lp-explore-results-list-item",
                        state=deps.state,
                        username=deps.username,
                        is_admin=deps.is_admin,
                        course_actions_builder=deps.course_actions_builder,
                        item_type=item_type,
                        on_set_tracking=deps.on_set_tracking,
                        on_clear_tracking=deps.on_clear_tracking,
                    )
            if len(visible_learning_items) > len(shown_learning_item_rows):
                with ui.row().classes("items-center justify-center w-full"):
                    ui.button("Show more learning items", on_click=deps.on_show_more_learning_items).props("outline dense")


def render_explore_empty_state(
    *,
    loaded_once: bool,
    on_refresh: Callable[[], Any],
    on_reset_filters: Callable[[], Any],
) -> None:
    """Render the Explore empty/error state block."""
    with ui.column().classes("w-full gap-2 lp-courses-section"):
        if not loaded_once:
            ui.label("Explore is unavailable right now").classes("lp-courses-section-title")
            ui.label("Refresh to reload courses, paths, videos, and articles.").classes("lp-courses-section-subtitle")
            ui.button("Refresh explore", on_click=on_refresh).props("outline")
            return
        ui.label("No matching results").classes("lp-courses-section-title")
        ui.label("Reset filters to widen the current explore view.").classes("lp-courses-section-subtitle")
        ui.button("Reset filters", on_click=on_reset_filters).props("outline")
