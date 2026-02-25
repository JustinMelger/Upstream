"""Detail dialog flows for Explore page cards."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.courses.detail_flow import open_course_details_dialog
from frontend.ui.nicegui.pages.courses.state import CoursesPageState


def open_explore_path_details_dialog(*, path_row: dict[str, Any], card_vm: Any) -> None:
    """Open a lightweight in-place path details dialog for Explore."""
    title = str(path_row.get("name") or "").strip() or "Path"
    description = str(path_row.get("description") or "").strip()
    with ui.dialog() as details_dialog:
        with ui.card().classes("lp-card lp-dialog w-[min(640px,95vw)]"):
            ui.label(title).classes("text-lg font-semibold")
            ui.label("Overview").classes("text-xs font-semibold mt-2").style("color: var(--lp-muted)")
            ui.label(description or "No description provided yet.").classes("text-sm").style("color: var(--lp-muted)")
            with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                if card_vm.shared_by:
                    ui.label(f"Shared by {card_vm.shared_by}").classes("lp-meta-chip lp-meta-chip--quiet")
                ui.label(card_vm.tracking_label_text).classes(card_vm.tracking_chip_cls)
            if card_vm.total_courses > 0:
                ui.label(f"Progress: {card_vm.completed}/{card_vm.total_courses} completed").classes("text-sm").style(
                    "color: var(--lp-muted)"
                )
                ui.linear_progress(card_vm.progress, show_value=False).classes("w-full mt-1")
            if card_vm.next_title:
                ui.label(f"Next: {card_vm.next_title}").classes("text-xs").style("color: var(--lp-muted)")
            with ui.row().classes("justify-end items-center gap-2 w-full mt-3"):
                ui.button("Close", on_click=details_dialog.close).props("outline")
    details_dialog.open()


def open_explore_article_details_dialog(*, article_row: dict[str, Any], focus_reviews: bool) -> None:
    """Open a lightweight in-place article details dialog for Explore."""
    title = str(article_row.get("title") or "").strip() or "Article"
    url = str(article_row.get("url") or "").strip()
    summary = str(article_row.get("summary") or "").strip()
    tags = parse_tags(str(article_row.get("tags") or ""))
    shared_by = str(article_row.get("created_by") or "").strip()
    created_at = str(article_row.get("created_at") or "").strip()
    with ui.dialog() as details_dialog:
        with ui.card().classes("lp-card lp-dialog w-[min(620px,95vw)]"):
            ui.label(title).classes("text-lg font-semibold")
            if url:
                ui.link(url, url).props("target=_blank").classes("text-sm")
            with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                if shared_by:
                    ui.label(f"Shared by {shared_by}").classes("lp-meta-chip lp-meta-chip--quiet")
                if created_at:
                    ui.label(created_at[:10]).classes("lp-meta-chip lp-meta-chip--quiet")
            if tags:
                with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                    for tag in tags[:6]:
                        ui.label(tag).classes("lp-meta-chip")
            ui.label("Overview").classes("text-xs font-semibold mt-2").style("color: var(--lp-muted)")
            ui.label(summary or "No summary provided yet.").classes("text-sm mt-1").style("color: var(--lp-muted)")
            if bool(focus_reviews):
                ui.label("Open Reviews from the overflow menu on Articles for full review management.").classes(
                    "text-xs mt-2"
                ).style("color: var(--lp-muted)")
            with ui.row().classes("justify-end items-center gap-2 w-full mt-3"):
                ui.button("Close", on_click=details_dialog.close).props("outline")
    details_dialog.open()


async def open_explore_course_details_dialog(
    *,
    course_id: int,
    focus_reviews: bool,
    username: str,
    is_admin: bool,
    state_tracking_by_course_id: dict[int, dict[str, Any]],
    review_summary_by_course_id: dict[int, dict[str, Any]],
    recommendation_summary_by_course_id: dict[int, dict[str, Any]],
    load_detail_bundle: Callable[[int, str], Awaitable[Any]],
    save_review: Callable[[int, int, str, str], Awaitable[dict[str, Any]]],
    delete_review: Callable[[int, int, str], Awaitable[bool]],
    on_set_tracking_status: Callable[[str], Awaitable[None]],
    on_clear_tracking_status: Callable[[], Awaitable[None]],
    on_tracking_changed: Callable[[str], None],
    normalize_course_view_mode: Callable[[bool], str],
    format_short_date: Callable[[Any], str],
) -> None:
    """Open course details dialog from Explore and sync local tracking state."""
    bridge_state = CoursesPageState(
        tracking_by_course_id=state_tracking_by_course_id,
        review_summary_by_course_id=review_summary_by_course_id,
        recommendation_summary_by_course_id=recommendation_summary_by_course_id,
    )
    await open_course_details_dialog(
        course_id=int(course_id),
        focus_reviews=bool(focus_reviews),
        username=username,
        is_admin=is_admin,
        state=bridge_state,
        load_detail_bundle=load_detail_bundle,
        save_review=save_review,
        delete_review=delete_review,
        current_status=str((state_tracking_by_course_id.get(int(course_id)) or {}).get("status") or ""),
        on_set_tracking_status=on_set_tracking_status,
        on_clear_tracking_status=on_clear_tracking_status,
        on_tracking_changed=on_tracking_changed,
        normalize_course_view_mode=normalize_course_view_mode,
        format_review_summary=lambda row: format_review_summary(row, style="fraction"),
        format_short_date=format_short_date,
    )
