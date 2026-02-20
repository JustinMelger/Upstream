"""Reusable UI sections for the Paths page."""

from __future__ import annotations

from typing import Any, Callable

from nicegui import ui


def render_paths_topbar(
    *,
    initial_scope: str,
    on_open_create_dialog: Callable[[], None],
) -> tuple[Any, Any, Any, Any]:
    """Render the Paths topbar and return interactive controls.

    Returns:
        Tuple of `(search_input, scope_filter, sort_filter, meta_label)`.
    """
    with ui.row().classes("lp-topbar lp-sticky-controls"):
        search_input = ui.input("Search paths").props("clearable debounce=300").style("flex: 1")
        with ui.row().classes("items-center gap-2").style("margin-left: auto"):
            ui.button("Share", on_click=on_open_create_dialog).props("dense")
            scope_filter = (
                ui.radio(
                    {"all": "All", "selected": "Selected"},
                    value=initial_scope,
                )
                .props("inline dense")
                .classes("text-sm")
            )
            sort_filter = (
                ui.select(
                    {
                        "": "Recommended",
                        "top_rated": "Top rated",
                        "most_reviewed": "Most reviewed",
                        "newest": "Recently added",
                        "name_az": "Name A-Z",
                    },
                    value="",
                    label=None,
                )
                .props("dense")
                .style("min-width: 180px")
            )
            meta = ui.label("").classes("lp-topbar-meta")
    return search_input, scope_filter, sort_filter, meta


def render_paths_filter_rail(
    *,
    on_refresh: Callable[[], Any],
    on_reset: Callable[[], Any],
    on_status_change: Callable[..., Any],
) -> tuple[Any, Any]:
    """Render the Paths filter rail controls.

    Returns:
        Tuple of `(status_filter, refresh_button)`.
    """
    with ui.row().classes("items-center justify-between w-full"):
        ui.label("Filters").classes("text-md font-semibold")
        refresh_btn = ui.button("Refresh", on_click=on_refresh).props("outline dense")

    ui.label("Tip: select a path to track progress.").classes("text-xs").style("color: var(--lp-muted)")

    status_filter = ui.select({"": "Any state"}, label="Path state", value="").props("dense").classes("w-full")
    status_filter.on("update:model-value", on_status_change)

    ui.element("div").style("flex: 1")
    ui.button("Clear", on_click=on_reset).props("outline dense").classes("w-full")
    return status_filter, refresh_btn
