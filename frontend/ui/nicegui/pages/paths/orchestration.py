"""State orchestration helpers for the paths page."""

from __future__ import annotations

from typing import Any, Callable

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.paths.actions import PathsFilterControls, reset_path_filter_controls
from frontend.ui.nicegui.pages.paths.state import PathsPageState, PathsPageUiState
from frontend.ui.nicegui.pages.paths.transitions import (
    begin_paths_load,
    clear_paths_state_on_load_error,
    finalize_paths_load,
)


def refresh_paths_list(
    *,
    ui_state: PathsPageUiState,
    recompute_facet_options: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_paths_list_ui: Callable[[], None],
) -> None:
    """Refresh list-level UI after filter updates."""
    ui_state.visible_count = int(ui_state.page_size)
    recompute_facet_options()
    refresh_active_filters()
    refresh_paths_list_ui()


def clear_path_filter_values(
    *,
    controls: PathsFilterControls,
    recompute_facet_options: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_paths_list_ui: Callable[[], None],
) -> None:
    """Reset all path filters and refresh related UI."""
    reset_path_filter_controls(controls=controls)
    recompute_facet_options()
    refresh_active_filters()
    refresh_paths_list_ui()


async def load_all_paths(
    *,
    ui_state: PathsPageUiState,
    controller_state: PathsPageState,
    controller: Any,
    refresh_btn: Any,
    meta: Any,
    create_course_ids: Any,
    compute_course_options: Callable[[list[dict[str, Any]] | None], dict[int, str]],
    recompute_facet_options: Callable[[], None],
    refresh_paths_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
    compute_meta_text: Callable[[int], str],
) -> None:
    """Reload all path page data and refresh controls."""
    if ui_state.loading:
        return
    ok = False
    load_start = begin_paths_load(page_size=ui_state.page_size)
    ui_state.loading = load_start.loading
    ui_state.visible_count = load_start.visible_count
    refresh_btn.disable()
    meta.text = load_start.meta_text
    refresh_paths_list_ui()
    try:
        await controller.load_all(state=controller_state)
        create_course_ids.options = compute_course_options(controller_state.courses)
        create_course_ids.update()
        recompute_facet_options()
        refresh_paths_list_ui()
        ok = True
    except ApiError as exc:
        notify_error(str(exc))
        clear_paths_state_on_load_error(state=controller_state)
        recompute_facet_options()
        refresh_paths_list_ui()
    finally:
        load_done = finalize_paths_load(ok=ok, path_count=len(controller_state.paths))
        meta.text = compute_meta_text(len(controller_state.paths))
        ui_state.loading = load_done.loading
        ui_state.loaded_once = load_done.loaded_once
        refresh_btn.enable()
        refresh_paths_list_ui()
