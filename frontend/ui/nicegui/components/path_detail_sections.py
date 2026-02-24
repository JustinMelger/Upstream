"""Reusable detail-dialog sections for Paths page."""

from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label


def render_path_detail_header(
    *,
    name: str,
    description: str,
    review_summary: str,
    recommendation_badge: str,
    recommended_by: str,
    latest_activity: str,
) -> None:
    """Render static header metadata for the path detail dialog."""
    ui.label(name).classes("text-xl font-semibold")
    ui.label(description).classes("text-sm text-gray-600")
    if review_summary:
        ui.label(f"Reviews: {review_summary}").classes("text-sm").style("color: var(--lp-muted)")
    if recommendation_badge:
        ui.label(recommendation_badge).classes("text-sm").style("color: var(--lp-muted)")
    if recommended_by:
        ui.label(f"Recommended by teammates: {recommended_by}").classes("text-xs").style("color: var(--lp-muted)")
    if latest_activity:
        ui.label(f"Latest activity: {latest_activity}").classes("text-xs").style("color: var(--lp-muted)")


def render_path_detail_learning_section(
    *,
    total_courses: int,
    completed: int,
    progress: float,
    milestone: str,
    milestone_class: str,
    impact: str,
    is_tracked: bool,
    tracking_label_text: str,
    next_title: str,
    on_open_next: Callable[[], Any] | None,
    courses_rows: list[dict[str, Any]],
) -> None:
    """Render progress + next step + course list for the detail dialog."""
    if total_courses > 0:
        ui.label(f"Progress: {completed}/{total_courses} completed").classes("text-sm").style("color: var(--lp-muted)")
        ui.linear_progress(progress, show_value=False).classes("w-full")
    with ui.row().classes("items-center gap-2 mt-2"):
        ui.label(milestone).classes(milestone_class)
        ui.label(impact).classes("text-xs").style("color: var(--lp-muted)")

    ui.label(f"State: {tracking_label_text if is_tracked else 'Not tracked'}").classes("text-sm")

    with ui.row().classes("items-center gap-2"):
        if next_title and on_open_next is not None:
            ui.label(f"Next step: {next_title}").classes("text-xs").style("color: var(--lp-muted)")
            ui.button("Continue path" if completed > 0 else "Start next course", on_click=on_open_next).props("outline")
        elif total_courses > 0:
            ui.label("Path completed").classes("lp-chip lp-chip--lime")

    ui.label("Courses").classes("text-lg font-semibold mt-4")
    if not courses_rows:
        ui.label("No courses in this path yet.").classes("text-sm").style("color: var(--lp-muted)")
        return
    with ui.column().classes("w-full gap-2"):
        for idx, course in enumerate(courses_rows, start=1):
            title = str(course.get("title") or "").strip() or f"Course #{int(course.get('id') or 0)}"
            provider = str(course.get("provider") or "").strip()
            category = str(course.get("category") or "").strip()
            reviews = str(course.get("reviews") or "").strip()
            with ui.card().classes("w-full lp-card"):
                ui.label(f"{idx}. {title}").classes("font-medium")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    if provider:
                        ui.label(provider).classes("lp-chip lp-chip--subtle")
                    if category:
                        ui.label(category).classes("lp-chip lp-chip--subtle")
                    if reviews:
                        ui.label(reviews).classes("lp-chip lp-chip--subtle")
                    ui.label(tracking_label(str(course.get("tracking_status") or ""))).classes(
                        tracking_chip_class(str(course.get("tracking_status") or ""))
                    )
