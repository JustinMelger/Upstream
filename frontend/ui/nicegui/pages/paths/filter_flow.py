"""Filter wiring helpers for the Paths page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.paths.actions import PathsFilterControls, recompute_path_status_filter
from frontend.ui.nicegui.pages.paths.filters import normalize_paths_filter_values
from frontend.ui.nicegui.pages.paths.orchestration import clear_path_filter_values, refresh_paths_list
from frontend.ui.nicegui.pages.paths.reducers import build_status_options, compute_status_counts
from frontend.ui.nicegui.pages.paths.state import PathsPageState, PathsPageUiState


def recompute_paths_facet_options(
    *,
    controls: PathsFilterControls,
    state: PathsPageState,
) -> None:
    """Recompute status facet options using the current local filter values."""
    normalized = normalize_paths_filter_values(
        scope_value=str(controls.scope_filter.value or "all"),
        search_value=str(controls.search_input.value or ""),
        status_value=str(controls.status_filter.value or "") if controls.status_filter is not None else "",
        sort_value=str(controls.sort_filter.value or ""),
    )
    recompute_path_status_filter(
        controls=controls,
        paths=state.paths,
        selected_by_id=state.selected_by_id,
        normalized_filters=normalized,
        compute_status_counts=compute_status_counts,
        build_status_options=build_status_options,
    )


def refresh_paths_filter_list(
    *,
    ui_state: PathsPageUiState,
    recompute_facet_options: Any,
    refresh_active_filters: Any,
    refresh_paths_list_ui: Any,
) -> None:
    """Refresh list-level UI after any filter update."""
    refresh_paths_list(
        ui_state=ui_state,
        recompute_facet_options=recompute_facet_options,
        refresh_active_filters=refresh_active_filters,
        refresh_paths_list_ui=refresh_paths_list_ui,
    )


def clear_paths_filters_and_refresh(
    *,
    controls: PathsFilterControls,
    recompute_facet_options: Any,
    refresh_active_filters: Any,
    refresh_paths_list_ui: Any,
) -> None:
    """Reset filters and refresh all list-level UI blocks."""
    clear_path_filter_values(
        controls=controls,
        recompute_facet_options=recompute_facet_options,
        refresh_active_filters=refresh_active_filters,
        refresh_paths_list_ui=refresh_paths_list_ui,
    )
