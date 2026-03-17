"""Item-level render helpers for Explore list sections."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import html
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_frame import (
    render_card_actions_row,
    render_card_content_column,
    render_card_main_row,
    render_card_topright,
)
from frontend.ui.nicegui.components.path_card import PathCardCallbacks, PathCardDisplay, render_path_card
from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.core.learning_items import learning_item_type_label
from frontend.ui.nicegui.pages.articles.actions import build_article_card_actions
from frontend.ui.nicegui.pages.articles.sections import render_article_card
from frontend.ui.nicegui.pages.articles.view_model import map_article_card_view
from frontend.ui.nicegui.pages.courses.sections import render_course_card
from frontend.ui.nicegui.pages.courses.ui_glue import resolve_tracking_status_value
from frontend.ui.nicegui.pages.courses.view_model import map_course_card_view
from frontend.ui.nicegui.pages.paths.actions import copy_path_link
from frontend.ui.nicegui.pages.paths.view_model import map_path_card_view


def render_course_item(
    *,
    course: dict[str, Any],
    item_classes: str,
    state: Any,
    username: str,
    is_admin: bool,
    course_actions_builder: Callable[[dict[str, Any], int, str], Any],
    item_type: str,
    on_set_tracking: Callable[[int, str], Awaitable[None]],
    on_clear_tracking: Callable[[int], Awaitable[None]],
) -> None:
    """Render one course card item for Explore."""
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
            force_media_slot=True,
            show_status_chip=False,
            show_compact_progress=True,
            show_context_meta=False,
            item_type_label=learning_item_type_label(item_type),
        )


def render_path_item(
    *,
    path: dict[str, Any],
    item_classes: str,
    state: Any,
    username: str,
    is_admin: bool,
    on_toggle_path_selection: Callable[[int], Awaitable[None]],
    open_path_details_dialog: Callable[[dict[str, Any], Any], None],
) -> None:
    """Render one path card item for Explore."""
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
        detail = state.selected_detail_by_path_id.get(path_id) or {}
        raw_course_ids = path.get("course_ids")
        inferred_total = 0
        if isinstance(raw_course_ids, list):
            inferred_total = len(raw_course_ids)
        else:
            try:
                inferred_total = int(path.get("course_count") or 0)
            except (TypeError, ValueError):
                inferred_total = 0
        total_courses = int(card_vm.total_courses or 0) if is_tracked else max(0, inferred_total)
        if total_courses <= 0 and isinstance(detail, dict):
            total_courses = len([c for c in list(detail.get("courses") or []) if isinstance(c, dict)])

        if not is_tracked:
            primary_label = "Track path"
        elif int(card_vm.completed or 0) <= 0:
            primary_label = "Start path"
        elif float(card_vm.progress or 0.0) >= 1.0:
            primary_label = "Open path"
        else:
            primary_label = "Continue path"

        async def _on_track_toggle() -> None:
            await on_toggle_path_selection(path_id)

        async def _open_path_details_inline() -> None:
            open_path_details_dialog(path, card_vm)

        def _open_path_reviews() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}?view=reviews")

        def _open_path_recommend() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}?view=reviews")

        def _copy_path_link() -> None:
            copy_path_link(path_id=path_id)

        def _open_path_edit() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}")

        def _open_path_delete() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}")

        async def _on_primary_action() -> None:
            if not is_tracked:
                await _on_track_toggle()
                return
            await _open_path_details_inline()

        render_path_card(
            display=PathCardDisplay(
                path_row=path,
                card_class_suffix=f"{card_vm.card_class_suffix} lp-path-card--compact lp-path-card--calm",
                is_new=False,
                is_updated=False,
                rating_badge="",
                recommendation_badge="",
                can_edit=can_edit,
                is_tracked=is_tracked,
                shared_by="",
                tracking_label_text=card_vm.tracking_label_text,
                tracking_chip_cls=card_vm.tracking_chip_cls,
                completed=card_vm.completed,
                total_courses=total_courses,
                progress=card_vm.progress,
                milestone=card_vm.milestone,
                milestone_class=card_vm.milestone_class,
                impact=card_vm.impact,
                next_title=card_vm.next_title,
                compact_calm=True,
            ),
            actions=PathCardCallbacks(
                on_review=_open_path_reviews,
                on_recommend=_open_path_recommend,
                on_copy_link=_copy_path_link,
                on_edit=_open_path_edit,
                on_delete=_open_path_delete,
                on_view=_open_path_details_inline,
                on_track_toggle=_on_track_toggle,
                track_toggle_label="",
                on_primary=_on_primary_action,
                primary_label=primary_label,
            ),
        )


def render_article_item(
    *,
    article: dict[str, Any],
    item_classes: str,
    state: Any,
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]],
) -> None:
    """Render one article card item for Explore."""
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
            compact_mode=True,
        )


def render_video_item(
    *,
    video: dict[str, Any],
    item_classes: str,
) -> None:
    """Render one video card item for Explore."""
    with ui.element("div").classes(item_classes):
        video_id = int(video.get("id") or 0)
        title = str(video.get("title") or "").strip()
        description = str(video.get("description") or "").strip()
        provider = str(video.get("provider") or "").strip()
        category = str(video.get("category") or "").strip()
        created_by = str(video.get("created_by") or "").strip()
        thumbnail_url = str(video.get("preview_image_url") or "").strip()
        source_url = str(video.get("url") or "").strip()

        with ui.card().classes("w-full lp-card lp-card--hover lp-article-card"):
            with render_card_topright():
                card_menu = apply_icon_button_a11y(
                    ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"),
                    label="Open video actions",
                    tooltip="Video actions",
                )
                with card_menu:
                    ui.menu_item("Open details", lambda: ui.navigate.to(f"/explore/videos/{video_id}"))
                    if source_url:
                        ui.menu_item("Open source", lambda: ui.navigate.to(source_url, new_tab=True))

            with render_card_main_row(classes="lp-article-card-main"):
                with render_card_content_column(classes="lp-article-card-content"):
                    ui.label(title).classes("text-lg font-semibold lp-card-title")

                    with ui.row().classes("items-center gap-2 flex-wrap lp-article-meta-row"):
                        ui.label("Video").classes("lp-meta-chip lp-meta-chip--quiet")
                        if provider:
                            ui.label(provider).classes("text-xs lp-card-subtitle lp-article-byline")
                        if created_by:
                            ui.label(f"Shared by {created_by}").classes("text-xs lp-card-subtitle lp-article-date")

                    with ui.row().classes("items-center gap-2 flex-wrap mt-1 lp-article-tag-row"):
                        chips = [value for value in [provider, category] if value]
                        if chips:
                            for chip in chips[:4]:
                                ui.label(chip).classes("lp-meta-chip")
                        else:
                            ui.label("").classes("lp-article-tag-placeholder")

                    if description:
                        ui.label(description).classes("text-sm text-gray-600 lp-card-body lp-course-summary")

                    def _render_actions() -> None:
                        ui.button(
                            "Open details",
                            on_click=lambda: ui.navigate.to(f"/explore/videos/{video_id}"),
                        ).props("dense")

                    render_card_actions_row(render_actions=_render_actions)

                if thumbnail_url:
                    safe_src = html.escape(thumbnail_url, quote=True)
                    with ui.element("div").classes("lp-article-media-slot"):
                        ui.html(
                            (
                                '<img class="lp-course-thumb lp-course-thumb--side lp-article-thumb" '
                                f'src="{safe_src}" '
                                'alt="Video thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                            ),
                            sanitize=False,
                        )
