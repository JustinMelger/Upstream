"""Course detail route renderer for Explore."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.components.status_chips import tracking_label, TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.action_feedback import tracking_cleared_message, tracking_set_message
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
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
    with ui.row().classes("items-center gap-2 flex-wrap lp-explore-detail-meta-row"):
        for label in [str(course.get("provider") or "").strip(), str(course.get("category") or "").strip()]:
            if label:
                ui.label(label).classes("lp-meta-chip")
        if str(course.get("duration_hours") or "").strip():
            ui.label(f"{course.get('duration_hours')}h").classes("lp-meta-chip")


def _rating_metrics(*, reviews: list[dict[str, Any]]) -> tuple[float, int]:
    ratings: list[int] = []
    for row in list(reviews or []):
        try:
            rating = int(row.get("rating") or 0)
        except (TypeError, ValueError):
            continue
        if 1 <= rating <= 5:
            ratings.append(rating)
    if not ratings:
        return 0.0, 0
    return float(sum(ratings)) / float(len(ratings)), len(ratings)


def _rating_stars(*, avg: float) -> str:
    rounded = max(0, min(5, int(round(float(avg)))))
    return ("★" * rounded) + ("☆" * (5 - rounded))


def _render_course_content_card(*, course: dict[str, Any], source_url: str, view_mode: str) -> None:
    with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Course Content").classes("text-base font-semibold")
            ui.icon("chevron_right").classes("lp-explore-detail-muted")

        if view_mode == "reviews":
            ui.label("Content hidden in reviews mode.").classes("lp-explore-detail-muted")
            return

        video_id = extract_youtube_video_id(source_url)
        if video_id:
            with ui.element("div").classes("lp-video-wrap mt-1"):
                ui.html(render_youtube_embed(youtube_embed_url(video_id)), sanitize=False)

        learning_outcomes = str(course.get("learning_outcomes") or "").strip()
        prerequisites = str(course.get("prerequisites") or "").strip()
        description = str(course.get("description") or "").strip()
        if learning_outcomes or prerequisites:
            if learning_outcomes:
                ui.label(learning_outcomes).classes("lp-explore-detail-body")
            if prerequisites:
                ui.label(f"Prerequisites: {prerequisites}").classes("lp-explore-detail-muted")
            return

        ui.label(description or "No content yet").classes("lp-explore-detail-muted")


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
            safe_notify(tracking_cleared_message(), type="positive")
            return
        await controller.set_tracking_status(course_id=course_id, status=selected)
        safe_notify(tracking_set_message(status=selected), type="positive")

    status_select.on("update:model-value", _on_status_change)


def _render_course_main_panel(
    *,
    controller: CoursesPageController,
    cid: int,
    username: str,
    is_admin: bool,
    course: dict[str, Any],
    reviews: list[dict[str, Any]],
    source_url: str,
    view_mode: str,
    avg_rating: float,
    review_count: int,
) -> None:
    with ui.column().classes("lp-explore-detail-main"):
        with ui.element("header").classes("lp-explore-detail-hero"):
            owner = str(course.get("created_by") or "").strip()
            ui.label("Course").classes("lp-explore-detail-eyebrow")
            ui.label(str(course.get("title") or "Course")).classes("lp-explore-detail-title")
            if review_count > 0:
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(_rating_stars(avg=avg_rating)).classes("lp-explore-rating-stars")
                    ui.label(f"{avg_rating:.1f}").classes("lp-explore-rating-score")
                    ui.label(f"{review_count} reviews").classes("lp-explore-detail-muted")
            if owner:
                ui.label(f"by {owner}").classes("lp-explore-detail-muted")
            if str(course.get("description") or "").strip():
                ui.label(str(course.get("description") or "")).classes("lp-explore-detail-body")
        _render_course_badges(course=course)
        _render_course_content_card(course=course, source_url=source_url, view_mode=view_mode)

        with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface lp-explore-reviews-panel"):
            if review_count <= 0:
                ui.label("Be the first to review this course.").classes("lp-explore-detail-muted")
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


def _render_course_info_panel(
    *,
    controller: CoursesPageController,
    cid: int,
    course: dict[str, Any],
    current_status: str,
    source_url: str,
    can_edit: bool,
    recommendations: list[dict[str, Any]],
) -> None:
    with ui.column().classes("lp-explore-detail-side lp-explore-info-card"):
        ui.label("Course Info").classes("text-base font-semibold")
        with ui.row().classes("items-center gap-2"):
            owner = str(course.get("created_by") or "").strip() or "Unknown"
            initials = "".join(part[:1] for part in owner.split() if part)[:2].upper() or owner[:2].upper()
            ui.label(initials).classes("lp-home-avatar-chip")
            ui.label(owner).classes("text-base")
        ui.label(f"Status: {tracking_label(current_status)}").classes("lp-explore-detail-muted")

        _bind_course_status_select(
            controller=controller,
            course_id=cid,
            current_status=current_status,
        )

        @guard_ui_action(title="Primary action failed")
        async def _run_primary_action() -> None:
            normalized_status = str(current_status or "").strip()
            if normalized_status == "":
                await controller.set_tracking_status(course_id=cid, status="interested")
                safe_notify(tracking_set_message(status="interested"), type="positive")
                return
            if normalized_status == "interested":
                await controller.set_tracking_status(course_id=cid, status="in_progress")
                safe_notify(tracking_set_message(status="in_progress"), type="positive")
                if source_url:
                    ui.navigate.to(source_url, new_tab=True)
                return
            if normalized_status == "in_progress":
                if source_url:
                    ui.navigate.to(source_url, new_tab=True)
                else:
                    safe_notify("No source URL available yet.", type="warning")
                return
            ui.navigate.to(f"/explore/courses/{cid}?view=reviews")

        primary_label = "Track course"
        if current_status == "interested":
            primary_label = "Start course"
        elif current_status == "in_progress":
            primary_label = "Continue course"
        elif current_status == "completed":
            primary_label = "Review course"
        ui.button(primary_label, on_click=_run_primary_action).props("unelevated")

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

            @guard_ui_action(title="Delete course failed")
            async def _delete_course() -> None:
                await controller.delete_course(course_id=cid)
                safe_notify("Course deleted", type="positive")
                ui.navigate.to("/explore?tab=courses")

            ui.button("Edit", icon="edit", on_click=_open_edit_course).props("outline")

        share_url = f"/explore/courses/{cid}"
        ui.button(
            "Share",
            icon="share",
            on_click=lambda: copy_text_to_clipboard(
                text=source_url or share_url,
                success_message=f"Course link copied: {share_url}",
            ),
        ).props("outline")
        if can_edit:
            ui.button("Delete", icon="delete", on_click=_delete_course).props("outline color=negative")

        if source_url:
            ui.button("Open source", on_click=lambda: ui.navigate.to(source_url, new_tab=True)).props("flat")
        if recommendations:
            ui.separator()
            ui.label("Recent recommendations").classes("text-sm font-semibold")
            for row in recommendations[:3]:
                by = str(row.get("created_by") or "").strip()
                note = str(row.get("note") or "").strip()
                text = f"{by}: {note}" if by and note else by or note
                if text:
                    ui.label(text).classes("lp-explore-detail-muted")


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
        avg_rating, review_count = _rating_metrics(reviews=reviews)

        with ui.row().classes("w-full items-start gap-4 lp-refresh-region"):
            _render_course_main_panel(
                controller=controller,
                cid=cid,
                username=username,
                is_admin=is_admin,
                course=course,
                reviews=reviews,
                source_url=source_url,
                view_mode=view_mode,
                avg_rating=avg_rating,
                review_count=review_count,
            )
            _render_course_info_panel(
                controller=controller,
                cid=cid,
                course=course,
                current_status=current_status,
                source_url=source_url,
                can_edit=can_edit,
                recommendations=recommendations,
            )
