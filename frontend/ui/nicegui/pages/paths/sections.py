"""UI sections for the Paths page."""

from __future__ import annotations

from typing import Any

from nicegui import ui


def render_paths_active_filter_chips(*, chips: list[Any], on_clear_key: Any) -> None:
    """Render removable active-filter chips for Paths."""
    if not chips:
        return

    with ui.row().classes("items-center gap-2 w-full"):
        for chip in chips:
            with ui.row().classes("items-center"):
                with ui.element("div").classes("lp-filter-chip"):
                    ui.label(str(chip.label or ""))
                    ui.button("×", on_click=lambda _key=chip.key: on_clear_key(str(_key))).props("dense flat")


def render_paths_empty_state(
    *,
    empty_state: str,
    on_browse_all: Any,
    on_refresh: Any,
    on_share: Any,
    on_browse_courses: Any,
    on_reset_all: Any,
) -> bool:
    """Render the matching empty-state block and return whether one was rendered."""
    if empty_state == "selected_empty":
        ui.label("No selected paths yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Browse paths and select one to start tracking.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Browse all paths", on_click=on_browse_all).props("outline")
            ui.button("Refresh", on_click=on_refresh).props("outline")
        return True

    if empty_state == "catalog_empty":
        ui.label("No paths yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Share the first path to get started.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Share a path", on_click=on_share).props("outline")
            ui.button("Browse courses", on_click=on_browse_courses).props("outline")
        return True

    if empty_state == "filters_empty":
        ui.label("No paths match your filters.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Reset all", on_click=on_reset_all).props("outline")
            ui.button("Refresh", on_click=on_refresh).props("outline")
        return True

    return False


def render_paths_collection_intro() -> None:
    """Render section heading above the paths result list."""
    with ui.column().classes("w-full gap-1 lp-courses-section"):
        ui.label("Recommended paths").classes("lp-courses-section-title")
        ui.label("Structured journeys to build momentum").classes("lp-courses-section-subtitle")
