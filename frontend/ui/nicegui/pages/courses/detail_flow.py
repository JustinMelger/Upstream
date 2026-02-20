"""Detail dialog flow for the Courses page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.pages.courses.state import CoursesPageState


async def open_course_details_dialog(
    *,
    course_id: int,
    focus_reviews: bool,
    username: str,
    is_admin: bool,
    state: CoursesPageState,
    load_detail_bundle: Callable[[int, str], Awaitable[Any]],
    save_review: Callable[[int, int, str, str], Awaitable[dict[str, Any]]],
    delete_review: Callable[[int, int, str], Awaitable[bool]],
    normalize_course_view_mode: Callable[[bool], str],
    format_review_summary: Callable[[dict[str, Any] | None], str],
    format_short_date: Callable[[Any], str],
) -> None:
    """Open course details dialog with reviews and recommendation metadata."""
    bundle = await load_detail_bundle(int(course_id), str(username or ""))
    course = dict(bundle.course or {})
    reviews = list(bundle.reviews or [])
    recommendations = list(bundle.recommendations or [])
    view_mode = normalize_course_view_mode(focus_reviews)

    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label(course.get("title") or "").classes("text-xl font-semibold")
        if str(course.get("description") or "").strip():
            ui.label(str(course.get("description") or "")).classes("text-sm text-gray-600")
        if view_mode != "reviews":
            summary_label = format_review_summary(state.review_summary_by_course_id.get(int(course_id)))
            provider = str(course.get("provider") or "").strip()
            category = str(course.get("category") or "").strip()
            language = str(course.get("language") or "").strip()
            shared_by = str(course.get("created_by") or "").strip()

            with ui.row().classes("items-center justify-between w-full mt-2"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    if provider:
                        ui.label(provider).classes("lp-meta-chip")
                    if category:
                        ui.label(category).classes("lp-meta-chip")
                    if language:
                        ui.label(language).classes("lp-meta-chip")
                    if shared_by:
                        ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                    if summary_label:
                        ui.label(f"★ {summary_label}").classes("lp-meta-chip")
                    rec_row = state.recommendation_summary_by_course_id.get(int(course_id)) or {}
                    rec_count = int(rec_row.get("recommendation_count") or 0) if isinstance(rec_row, dict) else 0
                    if rec_count > 0:
                        ui.label(f"↗ {rec_count} rec").classes("lp-meta-chip")
                if course.get("url"):
                    ui.button(
                        "Open link",
                        icon="open_in_new",
                        on_click=lambda u=str(course.get("url")): ui.navigate.to(u, new_tab=True),
                    ).props("outline dense")

            ui.separator()
            if recommendations:
                rec_by = sorted(
                    {
                        str(r.get("created_by") or "").strip()
                        for r in recommendations
                        if isinstance(r, dict) and str(r.get("created_by") or "").strip()
                    }
                )
                if rec_by:
                    ui.label(f"Recommended by {', '.join(rec_by[:3])}").classes("text-xs").style("color: var(--lp-muted)")
            learning_outcomes = str(course.get("learning_outcomes") or "").strip()
            prerequisites = str(course.get("prerequisites") or "").strip()
            if learning_outcomes or prerequisites:
                ui.separator()
                if learning_outcomes:
                    ui.label("Learning outcomes").classes("text-sm font-medium")
                    ui.label(learning_outcomes).classes("text-sm text-gray-600")
                if prerequisites:
                    ui.label("Prerequisites").classes("text-sm font-medium mt-2")
                    ui.label(prerequisites).classes("text-sm text-gray-600")
            latest_activity: str | None = None
            timestamps: list[str] = []
            for row in list(reviews) + list(recommendations):
                if not isinstance(row, dict):
                    continue
                created_at = str(row.get("created_at") or "").strip()
                if created_at:
                    timestamps.append(created_at)
            if timestamps:
                latest_activity = max(timestamps)
            if latest_activity:
                ui.label(f"Latest activity: {format_short_date(latest_activity)}").classes("text-xs").style(
                    "color: var(--lp-muted)"
                )

        def _sync_summary_from_reviews(current_reviews: list[dict[str, Any]]) -> None:
            ratings: list[int] = []
            for r in list(current_reviews or []):
                try:
                    ratings.append(int(r.get("rating") or 0))
                except (TypeError, ValueError):
                    continue
            if not ratings:
                state.review_summary_by_course_id[int(course_id)] = {
                    "course_id": int(course_id),
                    "avg_rating": 0.0,
                    "review_count": 0,
                }
            else:
                avg = float(sum(ratings)) / float(len(ratings))
                state.review_summary_by_course_id[int(course_id)] = {
                    "course_id": int(course_id),
                    "avg_rating": float(avg),
                    "review_count": int(len(ratings)),
                }

        async def _save_review(rating: int, text: str) -> dict[str, Any]:
            return await save_review(int(course_id), int(rating), str(text or ""), str(username or ""))

        async def _delete_review(review_id: int) -> bool:
            return await delete_review(int(course_id), int(review_id), str(username or ""))

        render_reviews_panel(
            username=username,
            is_admin=is_admin,
            reviews=reviews,
            section_title="Reviews",
            empty_text="No reviews yet.",
            on_save=_save_review,
            on_delete=_delete_review,
            format_date=format_short_date,
            on_changed=_sync_summary_from_reviews,
        )

        with ui.row().classes("justify-end mt-4"):
            ui.button("Close", on_click=dialog.close).props("outline")

    dialog.open()


async def open_course_details_flow(
    *,
    course_id: int,
    focus_reviews: bool,
    username: str,
    is_admin: bool,
    state: CoursesPageState,
    controller: Any,
    normalize_course_view_mode: Callable[[bool], str],
    format_short_date: Callable[[Any], str],
) -> None:
    """Open the course details dialog using controller/state callback wiring."""
    await open_course_details_dialog(
        course_id=int(course_id),
        focus_reviews=focus_reviews,
        username=username,
        is_admin=is_admin,
        state=state,
        load_detail_bundle=lambda _cid, _scope: controller.load_course_detail_bundle(
            course_id=int(_cid),
            cache_scope=str(_scope or ""),
        ),
        save_review=lambda _cid, _rating, _text, _scope: controller.save_course_review(
            course_id=int(_cid),
            rating=int(_rating),
            text=str(_text or ""),
            cache_scope=str(_scope or ""),
        ),
        delete_review=lambda _cid, _review_id, _scope: controller.delete_course_review(
            course_id=int(_cid),
            review_id=int(_review_id),
            cache_scope=str(_scope or ""),
        ),
        normalize_course_view_mode=normalize_course_view_mode,
        format_review_summary=lambda row: format_review_summary(row, style="fraction"),
        format_short_date=format_short_date,
    )
