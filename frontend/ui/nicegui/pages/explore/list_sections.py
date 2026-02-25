"""Result-section rendering helpers for Explore page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.path_card import render_path_card
from frontend.ui.nicegui.pages.articles.actions import build_article_card_actions
from frontend.ui.nicegui.pages.articles.sections import render_article_card
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.articles.view_model import map_article_card_view
from frontend.ui.nicegui.pages.courses.sections import render_course_card, render_courses_catalog
from frontend.ui.nicegui.pages.courses.ui_glue import resolve_tracking_status_value
from frontend.ui.nicegui.pages.courses.view_model import map_course_card_view
from frontend.ui.nicegui.pages.explore.sections import render_explore_article_rails
from frontend.ui.nicegui.pages.paths.actions import copy_path_link
from frontend.ui.nicegui.pages.paths.view_model import map_path_card_view


def render_explore_course_spotlight(
    *,
    enabled: bool,
    shown_courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    course_actions_builder: Callable[[dict[str, Any], int, str], Any],
    on_track: Callable[[int, str], Awaitable[None]],
) -> None:
    """Render compact Explore spotlight strip in cinema mode."""
    if not bool(enabled) or not shown_courses:
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
    state: Any,
    username: str,
    is_admin: bool,
    show_all_categories: bool,
    feature_explore_cinema: bool,
    course_actions_builder: Callable[[dict[str, Any], int, str], Any],
    on_set_tracking: Callable[[int, str], Awaitable[None]],
    on_clear_tracking: Callable[[int], Awaitable[None]],
    on_toggle_path_selection: Callable[[int], Awaitable[None]],
    open_path_details_dialog: Callable[[dict[str, Any], Any], None],
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]],
) -> None:
    """Render the mixed Explore sections for courses/paths/articles."""

    def _render_course_item(course: dict[str, Any], *, item_classes: str) -> None:
        with ui.element("div").classes(item_classes):
            course_id = int(course.get("id") or 0)
            tracked = state.tracking_by_course_id.get(course_id)
            url = str(course.get("url") or "").strip()
            can_edit = bool(is_admin or (str(course.get("created_by") or "") == username))
            card_vm = map_course_card_view(
                course_row=course,
                tracked_row=tracked if isinstance(tracked, dict) else None,
                review_summary_row=state.course_review_summary_by_course_id.get(course_id),
                recommendation_summary_row=state.course_recommendation_summary_by_course_id.get(course_id),
            )
            render_course_card(
                course_row=course,
                tracked_row=tracked if isinstance(tracked, dict) else None,
                card_vm=card_vm,
                can_edit=can_edit,
                has_url=bool(url),
                actions=course_actions_builder(course, course_id, url),
                is_tracked_course=lambda cid: int(cid) in state.tracking_by_course_id,
                resolve_status_value=resolve_tracking_status_value,
                on_set_status=on_set_tracking,
                on_clear_status=on_clear_tracking,
                has_video_preview=False,
                is_preview_open=False,
                preview_embed_url="",
                on_toggle_preview=lambda: None,
            )

    def _render_path_item(path: dict[str, Any], *, item_classes: str) -> None:
        with ui.element("div").classes(item_classes):
            path_id = int(path.get("id") or 0)
            is_tracked = path_id in state.selected_by_path_id
            can_edit = bool(is_admin or (str(path.get("created_by") or "") == username))
            card_vm = map_path_card_view(
                path_row=path,
                is_tracked=is_tracked,
                detail=state.selected_detail_by_path_id.get(path_id),
                tracking_by_course_id=dict(state.tracking_by_course_id or {}),
                review_summary_row=state.path_review_summary_by_id.get(path_id),
                recommendation_summary_row=state.path_recommendation_summary_by_id.get(path_id),
            )
            track_toggle_label = "Unselect" if is_tracked else "Select"

            async def _on_track_toggle() -> None:
                await on_toggle_path_selection(path_id)

            async def _open_path_details_inline() -> None:
                open_path_details_dialog(path, card_vm)

            def _open_path_reviews() -> None:
                ui.navigate.to(f"/paths?path_id={path_id}&view=reviews")

            def _open_path_recommend() -> None:
                ui.navigate.to(f"/paths?path_id={path_id}")

            def _copy_path_link() -> None:
                copy_path_link(path_id=path_id)

            def _open_path_edit() -> None:
                ui.navigate.to(f"/paths?path_id={path_id}")

            def _open_path_delete() -> None:
                ui.navigate.to(f"/paths?path_id={path_id}")

            render_path_card(
                path_row=path,
                card_class_suffix=f"{card_vm.card_class_suffix} lp-path-card--compact",
                is_new=card_vm.is_new,
                is_updated=card_vm.is_updated,
                rating_badge=card_vm.rating_badge,
                recommendation_badge=card_vm.recommendation_badge,
                can_edit=can_edit,
                shared_by=card_vm.shared_by,
                tracking_label_text=card_vm.tracking_label_text,
                tracking_chip_cls=card_vm.tracking_chip_cls,
                completed=card_vm.completed,
                total_courses=card_vm.total_courses,
                progress=card_vm.progress,
                milestone=card_vm.milestone,
                milestone_class=card_vm.milestone_class,
                impact=card_vm.impact,
                next_title=card_vm.next_title,
                on_review=_open_path_reviews,
                on_recommend=_open_path_recommend,
                on_copy_link=_copy_path_link,
                on_edit=_open_path_edit,
                on_delete=_open_path_delete,
                on_view=_open_path_details_inline,
                on_track_toggle=_on_track_toggle,
                track_toggle_label=track_toggle_label,
            )

    def _render_article_item(article: dict[str, Any], *, item_classes: str) -> None:
        with ui.element("div").classes(item_classes):
            article_id = int(article.get("id") or 0)
            vm = map_article_card_view(
                article_row=article,
                review_summary_row=state.article_review_summary_by_article_id.get(article_id),
            )
            actions = build_article_card_actions(
                article_row=article,
                on_open_details=open_article_details,
            )
            render_article_card(
                article_row=article,
                is_new=vm.is_new,
                tags=vm.tags[:4],
                summary_text=vm.summary_text,
                subtitle_text=vm.subtitle_text,
                thumbnail_url=vm.thumbnail_url,
                view_action=actions.on_view,
                review_action=actions.on_review,
            )

    if shown_courses:
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label("Course picks").classes("lp-courses-section-title")
        render_explore_course_spotlight(
            enabled=feature_explore_cinema,
            shown_courses=shown_courses,
            tracking_by_course_id=state.tracking_by_course_id,
            course_actions_builder=course_actions_builder,
            on_track=on_set_tracking,
        )
        render_courses_catalog(
            shown_page=shown_courses,
            render_course_item=_render_course_item,
            featured_title="Spotlight course",
            featured_subtitle="Top match for your current query",
            collection_title="More courses",
            show_featured=not feature_explore_cinema,
            max_groups=None if show_all_categories else 6,
            min_group_size=2,
            overflow_group_title="More for you",
            prioritize_larger_groups=True,
        )

    if shown_paths:
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label("Path picks").classes("lp-courses-section-title")
            ui.label("Top match for your current query").classes("lp-courses-section-subtitle")
        featured_path = shown_paths[0]
        remaining_paths = shown_paths[1:]
        with ui.element("div").classes("lp-courses-grid"):
            _render_path_item(featured_path, item_classes="lp-courses-grid-item")
        if remaining_paths:
            with ui.element("div").classes("lp-courses-grid"):
                for row in remaining_paths:
                    _render_path_item(row, item_classes="lp-courses-grid-item")

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
                _render_article_item(
                    featured_article,
                    item_classes="lp-courses-grid-item lp-courses-grid-item--featured",
                )

        if remaining_articles:
            render_explore_article_rails(
                shown_articles=remaining_articles,
                render_article_item=_render_article_item,
                max_groups=None if show_all_categories else 6,
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
