"""Course detail route renderer for Explore."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.courses.dialogs import open_edit_course_dialog
from frontend.ui.nicegui.pages.courses.media import extract_youtube_video_id, render_youtube_embed, youtube_embed_url
from frontend.ui.nicegui.pages.courses.ui_glue import format_short_date, parse_duration_hours
from frontend.ui.nicegui.pages.explore.detail_common import (
    parse_detail_id,
    parse_view_mode,
    render_breadcrumb,
    render_detail_scope,
)


async def _load_course_detail_payload(
    *,
    controller: CoursesPageController,
    course_id: int,
    username: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    bundle = await controller.load_course_detail_bundle(course_id=course_id, cache_scope=username)
    tracking_by_course_id = await controller.reload_tracking()
    return (
        dict(bundle.course or {}),
        list(bundle.reviews or []),
        list(bundle.recommendations or []),
        tracking_by_course_id,
    )


def _render_course_badges(*, course: dict[str, Any]) -> None:
    with ui.row().classes("items-center gap-2 flex-wrap"):
        for label in [str(course.get("provider") or "").strip(), str(course.get("category") or "").strip()]:
            if label:
                ui.label(label).classes("lp-meta-chip")
        if str(course.get("duration_hours") or "").strip():
            ui.label(f"{course.get('duration_hours')}h").classes("lp-meta-chip")
        if str(course.get("created_by") or "").strip():
            ui.label(f"Shared by {course.get('created_by')}").classes("lp-meta-chip lp-meta-chip--quiet")


def _render_course_overview(*, course: dict[str, Any], source_url: str, view_mode: str) -> None:
    _render_course_badges(course=course)
    video_id = extract_youtube_video_id(source_url)
    if video_id and view_mode != "reviews":
        with ui.element("div").classes("lp-video-wrap mt-2"):
            ui.html(render_youtube_embed(youtube_embed_url(video_id)), sanitize=False)
    if view_mode != "reviews":
        ui.label("Course content").classes("text-base font-semibold mt-2")
        learning_outcomes = str(course.get("learning_outcomes") or "").strip()
        prerequisites = str(course.get("prerequisites") or "").strip()
        if learning_outcomes:
            ui.label(learning_outcomes).classes("lp-explore-detail-body")
        if prerequisites:
            ui.label(f"Prerequisites: {prerequisites}").classes("lp-explore-detail-muted")


def _render_course_resources(*, course: dict[str, Any], recommendations: list[dict[str, Any]], source_url: str) -> None:
    ui.separator()
    ui.label("Resources").classes("text-sm font-semibold")
    if source_url:
        ui.link(str(course.get("title") or "Open source"), source_url).props("target=_blank")
    for row in recommendations[:5]:
        by = str(row.get("created_by") or "").strip()
        note = str(row.get("note") or "").strip()
        text = f"{by}: {note}" if by and note else by or note
        if text:
            ui.label(text).classes("lp-explore-detail-muted")


def _bind_course_status_select(
    *,
    controller: CoursesPageController,
    course_id: int,
    current_status: str,
) -> None:
    status_select = ui.select(
        {"": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
        value=current_status,
        label="Status",
    ).props("dense outlined")
    status_select.classes("lp-status-select")

    async def _on_status_change(e: Any) -> None:
        selected = str(getattr(e, "value", status_select.value) or "")
        if not selected:
            await controller.clear_tracking_status(course_id=course_id)
            safe_notify("Removed status", type="positive")
            return
        await controller.set_tracking_status(course_id=course_id, status=selected)
        safe_notify("Updated status", type="positive")

    status_select.on("update:model-value", _on_status_change)


async def render_explore_course_detail_page(*, store: SessionStore, api: ApiClient, course_id: str) -> None:
    """Render dedicated Explore course detail route."""
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    is_admin = str(user.get("role") or "") == "admin"
    view_mode = parse_view_mode()
    cid = parse_detail_id(course_id)

    with render_detail_scope(store=store, api=api):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        ui.element("div").classes("h-2")
        render_breadcrumb(label="Courses")
        if cid <= 0:
            ui.label("Invalid course id").classes("text-sm")
            return

        controller = CoursesPageController(api=api)
        try:
            course, reviews, recommendations, tracking_by_course_id = await _load_course_detail_payload(
                controller=controller,
                course_id=cid,
                username=username,
            )
        except ApiError as exc:
            ui.label(f"Course unavailable ({exc.status_code})").classes("text-sm")
            return

        current_status = str((tracking_by_course_id.get(cid) or {}).get("status") or "")
        source_url = str(course.get("url") or "").strip()
        can_edit = bool(is_admin or (str(course.get("created_by") or "").strip() == username))

        with ui.row().classes("w-full items-start gap-4"):
            with ui.column().classes("lp-explore-detail-main"):
                ui.label(str(course.get("title") or "Course")).classes("lp-explore-detail-title")
                if str(course.get("description") or "").strip():
                    ui.label(str(course.get("description") or "")).classes("lp-explore-detail-body")
                _render_course_overview(course=course, source_url=source_url, view_mode=view_mode)

                render_reviews_panel(
                    username=username,
                    is_admin=is_admin,
                    reviews=reviews,
                    on_save=lambda rating, text: controller.save_course_review(
                        course_id=cid,
                        rating=int(rating),
                        text=str(text or ""),
                        cache_scope=username,
                    ),
                    on_delete=lambda review_id: controller.delete_course_review(
                        course_id=cid,
                        review_id=int(review_id),
                        cache_scope=username,
                    ),
                    hooks=ReviewPanelHooks(format_date=format_short_date),
                )

            with ui.column().classes("lp-explore-detail-side"):
                ui.label("Actions").classes("text-sm font-semibold")
                if source_url:
                    ui.button("Open source", on_click=lambda: ui.navigate.to(source_url, new_tab=True)).props("outline")
                if can_edit:

                    @guard_ui_action(title="Open edit failed")
                    async def _open_edit_course() -> None:
                        async def _save(course_id: int, payload: dict[str, Any]) -> None:
                            await controller.update_course(course_id=int(course_id), payload=dict(payload or {}))
                            ui.navigate.to(f"/explore/courses/{cid}")

                        open_edit_course_dialog(
                            course=course,
                            parse_duration_hours=parse_duration_hours,
                            on_save=_save,
                        )

                    ui.button("Edit", icon="edit", on_click=_open_edit_course).props("outline")

                _bind_course_status_select(
                    controller=controller,
                    course_id=cid,
                    current_status=current_status,
                )
                _render_course_resources(
                    course=course,
                    recommendations=recommendations,
                    source_url=source_url,
                )
