"""Pure state-transition helpers for Paths page."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.paths.state import PathsPageState


@dataclass(slots=True)
class LoadTransition:
    """UI transition payload for page loading lifecycle."""

    loading: bool
    visible_count: int
    meta_text: str
    loaded_once: bool


@dataclass(slots=True)
class SelectionSnapshot:
    """Snapshot used for optimistic selection rollback."""

    path_id: int
    had_selected_row: bool
    selected_row: dict[str, Any] | None
    had_detail_row: bool
    detail_row: dict[str, Any] | None


def begin_paths_load(*, page_size: int) -> LoadTransition:
    """Transition payload for load-start."""
    return LoadTransition(loading=True, visible_count=int(page_size), meta_text="Loading...", loaded_once=False)


def complete_paths_load(*, path_count: int) -> LoadTransition:
    """Transition payload for successful load completion."""
    return LoadTransition(
        loading=False,
        visible_count=0,
        meta_text=f"{int(path_count)} paths",
        loaded_once=True,
    )


def fail_paths_load() -> LoadTransition:
    """Transition payload for failed load completion."""
    return LoadTransition(loading=False, visible_count=0, meta_text="Failed to load", loaded_once=True)


def finalize_paths_load(*, ok: bool, path_count: int) -> LoadTransition:
    """Return final load transition based on success/failure outcome."""
    return complete_paths_load(path_count=path_count) if bool(ok) else fail_paths_load()


def clear_paths_state_on_load_error(*, state: PathsPageState) -> None:
    """Reset paths page state on load failure."""
    state.paths = []
    state.selected_by_id = {}
    state.selected_detail_by_path_id = {}
    state.tracking_by_course_id = {}
    state.courses = []
    state.course_by_id = {}
    state.learning_item_options = {}
    state.path_review_summary_by_id = {}


def apply_optimistic_select(*, state: PathsPageState, path_id: int) -> SelectionSnapshot:
    """Optimistically mark a path as selected and return rollback snapshot."""
    pid = int(path_id)
    selected_row = state.selected_by_id.get(pid)
    detail_row = state.selected_detail_by_path_id.get(pid)
    snapshot = SelectionSnapshot(
        path_id=pid,
        had_selected_row=pid in state.selected_by_id,
        selected_row=deepcopy(selected_row) if isinstance(selected_row, dict) else None,
        had_detail_row=pid in state.selected_detail_by_path_id,
        detail_row=deepcopy(detail_row) if isinstance(detail_row, dict) else None,
    )
    if pid not in state.selected_by_id:
        state.selected_by_id[pid] = {"id": pid, "status": "interested"}
    return snapshot


def apply_optimistic_unselect(*, state: PathsPageState, path_id: int) -> SelectionSnapshot:
    """Optimistically unselect a path and return rollback snapshot."""
    pid = int(path_id)
    selected_row = state.selected_by_id.get(pid)
    detail_row = state.selected_detail_by_path_id.get(pid)
    snapshot = SelectionSnapshot(
        path_id=pid,
        had_selected_row=pid in state.selected_by_id,
        selected_row=deepcopy(selected_row) if isinstance(selected_row, dict) else None,
        had_detail_row=pid in state.selected_detail_by_path_id,
        detail_row=deepcopy(detail_row) if isinstance(detail_row, dict) else None,
    )
    state.selected_by_id.pop(pid, None)
    state.selected_detail_by_path_id.pop(pid, None)
    return snapshot


def rollback_optimistic_selection(*, state: PathsPageState, snapshot: SelectionSnapshot) -> None:
    """Rollback optimistic select/unselect mutation from snapshot."""
    pid = int(snapshot.path_id)
    if snapshot.had_selected_row and isinstance(snapshot.selected_row, dict):
        state.selected_by_id[pid] = deepcopy(snapshot.selected_row)
    elif not snapshot.had_selected_row:
        state.selected_by_id.pop(pid, None)

    if snapshot.had_detail_row and isinstance(snapshot.detail_row, dict):
        state.selected_detail_by_path_id[pid] = deepcopy(snapshot.detail_row)
    elif not snapshot.had_detail_row:
        state.selected_detail_by_path_id.pop(pid, None)
