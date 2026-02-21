"""Reusable path card component for the Paths page."""

from __future__ import annotations

from typing import Any, Callable

from nicegui import ui


def render_path_card(
    *,
    path_row: dict[str, Any],
    card_class_suffix: str,
    is_new: bool,
    is_updated: bool,
    rating_badge: str,
    recommendation_badge: str,
    can_edit: bool,
    shared_by: str,
    tracking_label_text: str,
    tracking_chip_cls: str,
    completed: int,
    total_courses: int,
    progress: float,
    milestone: str,
    milestone_class: str,
    impact: str,
    next_title: str,
    on_review: Callable[[], Any],
    on_recommend: Callable[[], Any],
    on_copy_link: Callable[[], Any],
    on_edit: Callable[[], Any],
    on_delete: Callable[[], Any],
    on_view: Callable[[], Any],
    on_track_toggle: Callable[[], Any],
    track_toggle_label: str,
) -> None:
    """Render a single path card."""
    with ui.card().classes(f"w-full lp-accent-card lp-card--hover lp-path-card{card_class_suffix}"):
        with ui.element("div").classes("lp-card-topright"):
            if is_new:
                ui.label("New").classes("lp-chip lp-chip--sky")
            elif is_updated:
                ui.label("Updated").classes("lp-chip lp-chip--teal")
            if rating_badge:
                ui.label(f"★ {rating_badge}").classes("lp-meta-chip")
            if recommendation_badge:
                ui.label(recommendation_badge).classes("lp-meta-chip")

            with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                ui.menu_item("Review", on_review)
                ui.menu_item("Recommend", on_recommend)
                ui.menu_item("Copy link", on_copy_link)
                if can_edit:
                    ui.menu_item("Edit", on_edit)
                    ui.menu_item("Delete", on_delete)

        ui.label(path_row.get("name") or "").classes("text-lg font-semibold lp-card-title")
        if str(path_row.get("description") or "").strip():
            ui.label(path_row.get("description") or "").classes("text-sm text-gray-600 lp-card-body")
        with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
            if shared_by:
                ui.label(f"Shared by {shared_by}").classes("text-xs lp-card-subtitle").style("color: var(--lp-muted)")
            ui.label(tracking_label_text).classes(tracking_chip_cls)

        if total_courses > 0:
            ui.label(f"{completed}/{total_courses} completed").classes("text-sm").style("color: var(--lp-muted)")
            ui.linear_progress(progress, show_value=False).classes("w-full")
            with ui.row().classes("items-center gap-2"):
                ui.label(milestone).classes(f"{milestone_class} lp-path-milestone")
                ui.label(impact).classes("text-xs").style("color: var(--lp-muted)")
            if next_title:
                ui.label(f"Next: {next_title}").classes("text-xs").style("color: var(--lp-muted)")

        with ui.row().classes("items-center gap-2 mt-2") as actions_row:
            actions_row.classes("lp-card-actions")
            ui.button("", icon="visibility", on_click=on_view).props("outline dense").tooltip("View")
            ui.button(track_toggle_label, on_click=on_track_toggle).props("outline dense")
