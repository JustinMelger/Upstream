"""Reusable path card component for the Paths page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from nicegui import ui

from frontend.ui.nicegui.components.card_frame import (
    render_card_actions_row,
    render_card_content_column,
    render_card_topright,
)


@dataclass(slots=True)
class PathCardDisplay:
    """Display fields required for rendering one path card."""

    path_row: dict[str, Any]
    card_class_suffix: str
    is_new: bool
    is_updated: bool
    rating_badge: str
    recommendation_badge: str
    can_edit: bool
    shared_by: str
    tracking_label_text: str
    tracking_chip_cls: str
    completed: int
    total_courses: int
    progress: float
    milestone: str
    milestone_class: str
    impact: str
    next_title: str


@dataclass(slots=True)
class PathCardCallbacks:
    """Action callbacks required for one path card."""

    on_review: Callable[[], Any]
    on_recommend: Callable[[], Any]
    on_copy_link: Callable[[], Any]
    on_edit: Callable[[], Any]
    on_delete: Callable[[], Any]
    on_view: Callable[[], Any]
    on_track_toggle: Callable[[], Any]
    track_toggle_label: str


def render_path_card(
    *,
    display: PathCardDisplay,
    actions: PathCardCallbacks,
) -> None:
    """Render a single path card."""
    suffix = str(display.card_class_suffix or "")
    compact_mode = "lp-path-card--compact" in suffix
    with ui.card().classes(f"w-full lp-accent-card lp-card--hover lp-path-card{suffix}"):
        with render_card_topright():
            if display.is_new:
                ui.label("New").classes("lp-chip lp-chip--sky")
            elif display.is_updated:
                ui.label("Updated").classes("lp-chip lp-chip--teal")
            if display.rating_badge:
                ui.label(f"★ {display.rating_badge}").classes("lp-meta-chip lp-meta-chip--rating")
            if display.recommendation_badge:
                ui.label(display.recommendation_badge).classes("lp-meta-chip")

            with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                ui.menu_item("Review", actions.on_review)
                ui.menu_item("Recommend", actions.on_recommend)
                ui.menu_item("Copy link", actions.on_copy_link)
                if display.can_edit:
                    ui.menu_item("Edit", actions.on_edit)
                    ui.menu_item("Delete", actions.on_delete)

        with render_card_content_column(classes="lp-path-card-content lp-course-card-stack"):
            ui.label(display.path_row.get("name") or "").classes("text-lg font-semibold lp-card-title")
            with ui.row().classes("items-center gap-2 flex-wrap mt-1 lp-path-meta-row"):
                if display.shared_by:
                    ui.label(f"Shared by {display.shared_by}").classes("text-xs lp-card-subtitle").style(
                        "color: var(--lp-muted)"
                    )
                ui.label(display.tracking_label_text).classes(display.tracking_chip_cls)

            if display.total_courses > 0:
                if compact_mode:
                    with ui.row().classes("items-center gap-2 flex-wrap w-full lp-path-context-line"):
                        ui.label(f"{display.completed}/{display.total_courses} completed").classes(
                            "text-xs lp-path-progress-label"
                        )
                        ui.label(display.milestone).classes(f"{display.milestone_class} lp-path-milestone")
                    if display.next_title:
                        ui.label(f"Next: {display.next_title}").classes("text-xs lp-path-next-line").style(
                            "color: var(--lp-muted)"
                        )
                else:
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label("Path progress").classes("text-xs lp-path-progress-label")
                        ui.label(f"{display.completed}/{display.total_courses} completed").classes(
                            "text-sm lp-path-progress-count"
                        ).style("color: var(--lp-muted)")
                    ui.linear_progress(display.progress, show_value=False).classes("w-full lp-path-progress-bar")
                    with ui.row().classes("items-center gap-2 lp-path-milestone-row"):
                        ui.label(display.milestone).classes(f"{display.milestone_class} lp-path-milestone")
                        ui.label(display.impact).classes("text-xs").style("color: var(--lp-muted)")
                    if display.next_title:
                        ui.label(f"Next: {display.next_title}").classes("text-xs").style("color: var(--lp-muted)")
            elif compact_mode:
                ui.label("Select to track milestones").classes("text-xs lp-card-subtitle lp-path-context-line")
            if (not compact_mode) and str(display.path_row.get("description") or "").strip():
                ui.label(display.path_row.get("description") or "").classes(
                    "text-sm text-gray-600 lp-card-body lp-path-description"
                )

            def _render_actions() -> None:
                ui.button("Open", on_click=actions.on_view).props("dense")
                ui.button(actions.track_toggle_label, on_click=actions.on_track_toggle).props("outline dense")

            render_card_actions_row(render_actions=_render_actions)
