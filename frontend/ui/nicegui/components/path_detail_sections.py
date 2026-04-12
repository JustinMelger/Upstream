"""Reusable detail-dialog sections for Paths page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from nicegui import ui

from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label


def render_path_detail_header(
    *,
    name: str,
    description: str,
    review_summary: str,
    latest_activity: str,
) -> None:
    """Render static header metadata for the path detail dialog."""
    ui.label(name).classes("text-xl font-semibold")
    ui.label(description).classes("text-sm text-gray-600")
    if review_summary:
        ui.label(f"Reviews: {review_summary}").classes("text-sm").style("color: var(--lp-muted)")
    if latest_activity:
        ui.label(f"Latest activity: {latest_activity}").classes("text-xs").style("color: var(--lp-muted)")


@dataclass(frozen=True, slots=True)
class PathDetailLearningView:
    """View model for path learning/progress section."""

    total_courses: int
    completed: int
    progress: float
    milestone: str
    milestone_class: str
    impact: str
    is_tracked: bool
    tracking_label_text: str
    next_title: str
    item_rows: list[dict[str, Any]]


def render_path_detail_learning_section(*, view: PathDetailLearningView, on_open_next: Callable[[], Any] | None) -> None:
    """Render progress + next step + learning-item list for the detail dialog."""
    if view.total_courses > 0:
        ui.label(f"Progress: {view.completed}/{view.total_courses} completed").classes("text-sm").style(
            "color: var(--lp-muted)"
        )
        ui.linear_progress(view.progress, show_value=False).classes("w-full")
    with ui.row().classes("items-center gap-2 mt-2"):
        ui.label(view.milestone).classes(view.milestone_class)
        ui.label(view.impact).classes("text-xs").style("color: var(--lp-muted)")

    ui.label(f"State: {view.tracking_label_text if view.is_tracked else 'Not tracked'}").classes("text-sm")

    with ui.row().classes("items-center gap-2"):
        if view.next_title and on_open_next is not None:
            ui.label(f"Next step: {view.next_title}").classes("text-xs").style("color: var(--lp-muted)")
            ui.button("Continue path" if view.completed > 0 else "Start next course", on_click=on_open_next).props("outline")
        elif view.total_courses > 0:
            ui.label("Path completed").classes("lp-chip lp-chip--lime")

    ui.label("Learning items").classes("text-lg font-semibold mt-4")
    if not view.item_rows:
        ui.label("No learning items in this path yet.").classes("text-sm").style("color: var(--lp-muted)")
        return
    with ui.column().classes("w-full gap-2"):
        for idx, item in enumerate(view.item_rows, start=1):
            item_type = str(item.get("type") or "course").strip().lower() or "course"
            fallback_label = item_type.capitalize()
            title = str(item.get("title") or "").strip() or f"{fallback_label} #{int(item.get('id') or 0)}"
            provider = str(item.get("provider") or "").strip()
            category = str(item.get("category") or "").strip()
            reviews = str(item.get("reviews") or "").strip()
            status = str(item.get("tracking_status") or "")
            with ui.card().classes("w-full lp-card"):
                ui.label(f"{idx}. {title}").classes("font-medium")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(item_type.capitalize()).classes("lp-chip lp-chip--subtle")
                    if provider:
                        ui.label(provider).classes("lp-chip lp-chip--subtle")
                    if category:
                        ui.label(category).classes("lp-chip lp-chip--subtle")
                    if reviews:
                        ui.label(reviews).classes("lp-chip lp-chip--subtle")
                    if item_type == "course":
                        ui.label(tracking_label(status)).classes(tracking_chip_class(status))
