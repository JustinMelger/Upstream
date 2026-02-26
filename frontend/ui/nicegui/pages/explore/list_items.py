"""Item-level render helpers for Explore list sections."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.path_card import PathCardCallbacks, PathCardDisplay, render_path_card
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
        track_toggle_label = "Unselect" if is_tracked else "Select"

        async def _on_track_toggle() -> None:
            await on_toggle_path_selection(path_id)

        async def _open_path_details_inline() -> None:
            open_path_details_dialog(path, card_vm)

        def _open_path_reviews() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}?view=reviews")

        def _open_path_recommend() -> None:
            ui.navigate.to(f"/manage/paths?path_id={path_id}")

        def _copy_path_link() -> None:
            copy_path_link(path_id=path_id)

        def _open_path_edit() -> None:
            ui.navigate.to(f"/manage/paths?path_id={path_id}")

        def _open_path_delete() -> None:
            ui.navigate.to(f"/manage/paths?path_id={path_id}")

        render_path_card(
            display=PathCardDisplay(
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
            ),
            actions=PathCardCallbacks(
                on_review=_open_path_reviews,
                on_recommend=_open_path_recommend,
                on_copy_link=_copy_path_link,
                on_edit=_open_path_edit,
                on_delete=_open_path_delete,
                on_view=_open_path_details_inline,
                on_track_toggle=_on_track_toggle,
                track_toggle_label=track_toggle_label,
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
