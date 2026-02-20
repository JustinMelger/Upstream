from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths.state import PathsPageState
from frontend.ui.nicegui.pages.paths.transitions import (
    apply_optimistic_select,
    apply_optimistic_unselect,
    begin_paths_load,
    clear_paths_state_on_load_error,
    complete_paths_load,
    fail_paths_load,
    finalize_paths_load,
    rollback_optimistic_selection,
)


@pytest.mark.unit
def test_load_transitions_are_stable() -> None:
    start = begin_paths_load(page_size=10)
    assert start.loading is True
    assert start.visible_count == 10
    assert start.meta_text == "Loading..."
    assert start.loaded_once is False

    done = complete_paths_load(path_count=7)
    assert done.loading is False
    assert done.meta_text == "7 paths"
    assert done.loaded_once is True

    failed = fail_paths_load()
    assert failed.loading is False
    assert failed.meta_text == "Failed to load"
    assert failed.loaded_once is True

    assert finalize_paths_load(ok=True, path_count=3).meta_text == "3 paths"
    assert finalize_paths_load(ok=False, path_count=3).meta_text == "Failed to load"


@pytest.mark.unit
def test_clear_paths_state_on_load_error_resets_all_collections() -> None:
    state = PathsPageState(
        paths=[{"id": 1}],
        selected_by_id={1: {"id": 1}},
        selected_detail_by_path_id={1: {"id": 1, "courses": []}},
        tracking_by_course_id={10: {"course_id": 10, "status": "interested"}},
        courses=[{"id": 10}],
        course_by_id={10: {"id": 10}},
        path_review_summary_by_id={1: {"path_id": 1, "review_count": 1}},
        path_recommendation_summary_by_id={1: {"path_id": 1, "recommendation_count": 1}},
    )
    clear_paths_state_on_load_error(state=state)
    assert state.paths == []
    assert state.selected_by_id == {}
    assert state.selected_detail_by_path_id == {}
    assert state.tracking_by_course_id == {}
    assert state.courses == []
    assert state.course_by_id == {}
    assert state.path_review_summary_by_id == {}
    assert state.path_recommendation_summary_by_id == {}


@pytest.mark.unit
def test_optimistic_select_and_rollback_restore_previous_state() -> None:
    state = PathsPageState(
        selected_by_id={3: {"id": 3, "status": "interested"}},
        selected_detail_by_path_id={3: {"id": 3, "courses": []}},
    )
    snap = apply_optimistic_select(state=state, path_id=7)
    assert 7 in state.selected_by_id
    rollback_optimistic_selection(state=state, snapshot=snap)
    assert 7 not in state.selected_by_id
    assert state.selected_by_id[3]["status"] == "interested"


@pytest.mark.unit
def test_optimistic_unselect_and_rollback_restore_removed_rows() -> None:
    state = PathsPageState(
        selected_by_id={8: {"id": 8, "status": "in_progress"}},
        selected_detail_by_path_id={8: {"id": 8, "courses": [{"id": 1}]}},
    )
    snap = apply_optimistic_unselect(state=state, path_id=8)
    assert 8 not in state.selected_by_id
    assert 8 not in state.selected_detail_by_path_id
    rollback_optimistic_selection(state=state, snapshot=snap)
    assert state.selected_by_id[8]["status"] == "in_progress"
    assert state.selected_detail_by_path_id[8]["id"] == 8


@pytest.mark.unit
def test_optimistic_snapshot_rollback_uses_deep_copy_for_nested_payloads() -> None:
    state = PathsPageState(
        selected_by_id={8: {"id": 8, "status": "in_progress"}},
        selected_detail_by_path_id={8: {"id": 8, "courses": [{"id": 1}, {"id": 2}]}},
    )
    snap = apply_optimistic_select(state=state, path_id=8)
    # Mutate nested state payload after snapshot capture.
    state.selected_detail_by_path_id[8]["courses"][0]["id"] = 999
    rollback_optimistic_selection(state=state, snapshot=snap)
    courses = list(state.selected_detail_by_path_id[8].get("courses") or [])
    assert int(courses[0]["id"]) == 1
