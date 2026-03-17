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


_DEFAULT_COURSE_CAP = 8
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
    open_path_details_dialog: Callable[[dict[str, Any], Any], None]
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]]
    learning_items_visible_limit: int
    on_show_more_learning_items: Callable[[], None]


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
    shown_learning_items: list[ExploreLearningItemEntry],
    deps: ExploreSectionsDeps,
) -> None:
    """Render the mixed Explore sections for courses/paths/articles."""
    course_cap = 16 if deps.show_all_categories else _DEFAULT_COURSE_CAP
    path_cap = 12 if deps.show_all_categories else _DEFAULT_PATH_CAP
    learning_item_cap = 16 if deps.show_all_categories else _DEFAULT_LEARNING_ITEM_CAP

    visible_courses = shown_courses[:course_cap]
    visible_paths = shown_paths[:path_cap]
    visible_learning_items = shown_learning_items[:learning_item_cap]

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

    if visible_learning_items:
        limit = max(1, int(deps.learning_items_visible_limit or _DEFAULT_LEARNING_ITEM_CAP))
        shown_learning_item_rows = visible_learning_items[:limit]

        with ui.element("section").classes("w-full lp-explore-section-block"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-1"):
                    ui.label("Learning items").classes("lp-courses-section-title")
                    ui.label("Browse all learning items.").classes("lp-courses-section-subtitle")
            with ui.element("div").classes("lp-courses-grid lp-explore-course-grid"):
                for item in shown_learning_item_rows:
                    row = dict(item.row or {})
                    item_type = str(item.learning_item_type or "").strip().lower()
                    if item_type == "article":
                        render_article_item(
                            article=row,
                            item_classes="lp-courses-grid-item",
                            state=deps.state,
                            open_article_details=deps.open_article_details,
                        )
                        continue
                    if item_type == "video":
                        render_video_item(
                            video=row,
                            item_classes="lp-courses-grid-item",
                        )
                        continue
                    render_course_item(
                        course=row,
                        item_classes="lp-courses-grid-item",
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
            ui.label("Discovery feed unavailable").classes("lp-courses-section-title")
            ui.label("Explore could not load right now. Refresh to retry.").classes("lp-courses-section-subtitle")
            ui.button("Refresh explore", on_click=on_refresh).props("outline")
            return
        ui.label("No matches in Explore").classes("lp-courses-section-title")
        ui.label("Reset filters to widen your discovery results.").classes("lp-courses-section-subtitle")
        ui.button("Reset filters", on_click=on_reset_filters).props("outline")
