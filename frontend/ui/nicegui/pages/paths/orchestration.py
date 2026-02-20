"""State orchestration helpers for the paths page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.paths.actions import PathsFilterControls, reset_path_filter_controls
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
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


async def run_select_path_flow(
    *,
    path_id: int,
    controller: PathsPageController,
    state: PathsPageState,
    reload_selected: Callable[[], Awaitable[bool]],
    ensure_selected_detail: Callable[[int], Awaitable[None]],
    reload_tracking: Callable[[], Awaitable[None]],
    on_scope_selected: Callable[[], None],
    notify: Callable[[str, str], None],
    refresh_paths_list_ui: Callable[[], None],
    open_details: Callable[[int], Awaitable[None]],
) -> bool:
    """Execute path-selection side effects outside the page module."""
    seeded, detail = await controller.select_path(path_id=int(path_id), state=state)
    reloaded = await reload_selected()
    if not reloaded:
        notify("Path selected, but selected list failed to refresh", "warning")
    if isinstance(detail, dict):
        state.selected_detail_by_path_id[int(path_id)] = detail
    else:
        await ensure_selected_detail(int(path_id))
    if seeded > 0:
        await reload_tracking()
    on_scope_selected()
    msg = "Path added to My learning"
    if seeded > 0:
        msg = f"{msg} · {seeded} course(s) set to Interested"
    notify(msg, "positive")
    refresh_paths_list_ui()
    await open_details(int(path_id))
    return True


async def run_unselect_path_flow(
    *,
    path_id: int,
    controller: PathsPageController,
    state: PathsPageState,
    reload_selected: Callable[[], Awaitable[bool]],
    notify: Callable[[str, str], None],
    refresh_paths_list_ui: Callable[[], None],
) -> bool:
    """Execute path-unselection side effects outside the page module."""
    await controller.unselect_path(path_id=int(path_id))
    reloaded = await reload_selected()
    if not reloaded:
        notify("Path untracked, but selected list failed to refresh", "warning")
    state.selected_detail_by_path_id.pop(int(path_id), None)
    refresh_paths_list_ui()
    return True


async def refresh_path_recommendation_summary(
    *,
    path_id: int,
    controller: PathsPageController,
    state: PathsPageState,
    refresh_paths_list_ui: Callable[[], None],
) -> None:
    """Refresh recommendation summary map entry for a single path."""
    row = await controller.load_recommendation_summary_for_path(path_id=int(path_id))
    if isinstance(row, dict):
        state.path_recommendation_summary_by_id[int(path_id)] = row
    else:
        state.path_recommendation_summary_by_id.pop(int(path_id), None)
    refresh_paths_list_ui()


async def perform_create_path(
    *,
    payload: dict[str, Any],
    controller: PathsPageController,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Create a path, then reload page data."""
    await controller.create_path(payload=dict(payload or {}))
    await reload_page()


async def perform_update_path(
    *,
    path_id: int,
    payload: dict[str, Any],
    controller: PathsPageController,
    reload_page: Callable[[], Awaitable[None]],
    refresh_paths_list_ui: Callable[[], None],
) -> None:
    """Update a path, then reload page data and refresh list UI."""
    await controller.update_path(path_id=int(path_id), payload=dict(payload or {}))
    await reload_page()
    refresh_paths_list_ui()


async def perform_delete_path(
    *,
    path_id: int,
    controller: PathsPageController,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Delete a path, then reload page data."""
    await controller.delete_path(path_id=int(path_id))
    await reload_page()


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
