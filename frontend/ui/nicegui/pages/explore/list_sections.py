"""Result-section rendering helpers for Explore page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.courses.sections import render_courses_catalog
from frontend.ui.nicegui.pages.explore.list_items import render_article_item, render_course_item, render_path_item
from frontend.ui.nicegui.pages.explore.sections import render_explore_article_rails


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

    if shown_courses:
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label("Course picks").classes("lp-courses-section-title")
        render_explore_course_spotlight(
            shown_courses=shown_courses,
            tracking_by_course_id=deps.state.tracking_by_course_id,
            course_actions_builder=deps.course_actions_builder,
            on_track=deps.on_set_tracking,
        )
        render_courses_catalog(
            shown_page=shown_courses,
            render_course_item=lambda course, item_classes: render_course_item(
                course=course,
                item_classes=item_classes,
                state=deps.state,
                username=deps.username,
                is_admin=deps.is_admin,
                course_actions_builder=deps.course_actions_builder,
                on_set_tracking=deps.on_set_tracking,
                on_clear_tracking=deps.on_clear_tracking,
            ),
            featured_title="Spotlight course",
            featured_subtitle="Top match for your current query",
            collection_title="More courses",
            show_featured=False,
            max_groups=None if deps.show_all_categories else 6,
            min_group_size=2,
            overflow_group_title="More for you",
            prioritize_larger_groups=True,
        )

    if shown_paths:
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label("Path picks").classes("lp-courses-section-title")
            ui.label("Top match for your current query").classes("lp-courses-section-subtitle")
        with ui.element("div").classes("lp-courses-grid"):
            for idx, row in enumerate(shown_paths):
                item_classes = "lp-courses-grid-item lp-courses-grid-item--featured" if idx == 0 else "lp-courses-grid-item"
                render_path_item(
                    path=row,
                    item_classes=item_classes,
                    state=deps.state,
                    username=deps.username,
                    is_admin=deps.is_admin,
                    on_toggle_path_selection=deps.on_toggle_path_selection,
                    open_path_details_dialog=deps.open_path_details_dialog,
                )

    if shown_articles:
        grouped_articles: list[dict[str, Any]] = []
        for row in shown_articles:
            tags = parse_tags(str(row.get("tags") or ""))
            group_name = str(tags[0] if tags else "General")
            grouped_articles.append({**row, "_explore_group": group_name})

        featured_article = grouped_articles[0]
        remaining_articles = grouped_articles[1:]
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label("Article picks").classes("lp-courses-section-title")
            ui.label("Top match for your current query").classes("lp-courses-section-subtitle")
            with ui.element("div").classes("lp-courses-grid"):
                render_article_item(
                    article=featured_article,
                    item_classes="lp-courses-grid-item lp-courses-grid-item--featured",
                    state=deps.state,
                    open_article_details=deps.open_article_details,
                )

        if remaining_articles:
            render_explore_article_rails(
                shown_articles=remaining_articles,
                render_article_item=lambda article, item_classes: render_article_item(
                    article=article,
                    item_classes=item_classes,
                    state=deps.state,
                    open_article_details=deps.open_article_details,
                ),
                max_groups=None if deps.show_all_categories else 6,
                min_group_size=2,
                overflow_group_title="More for you",
                prioritize_larger_groups=True,
            )


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
            ui.button("Refresh", on_click=on_refresh).props("outline")
            return
        ui.label("No matches in Explore").classes("lp-courses-section-title")
        ui.label("Adjust search scope or filters to discover more content.").classes("lp-courses-section-subtitle")
        ui.button("Reset filters", on_click=on_reset_filters).props("outline")
