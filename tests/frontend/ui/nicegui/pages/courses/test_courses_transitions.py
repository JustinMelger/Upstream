from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.state import CoursesPageState
from frontend.ui.nicegui.pages.courses.transitions import (
    apply_optimistic_tracking_clear,
    apply_optimistic_tracking_set,
    begin_courses_load,
    clear_courses_state_on_load_error,
    complete_courses_load,
    fail_courses_load,
    finalize_courses_load,
    rollback_optimistic_tracking,
)


@pytest.mark.unit
def test_course_load_transitions_are_stable() -> None:
    start = begin_courses_load(page_size=10)
    assert start.loading is True
    assert start.visible_count == 10
    assert start.meta_text == "Loading..."
    assert start.loaded_once is False

    done = complete_courses_load(course_count=7)
    assert done.loading is False
    assert done.meta_text == "7 courses"
    assert done.loaded_once is True

    failed = fail_courses_load()
    assert failed.loading is False
    assert failed.meta_text == "0 courses"
    assert failed.loaded_once is True

    assert finalize_courses_load(ok=True, course_count=3).meta_text == "3 courses"
    assert finalize_courses_load(ok=False, course_count=3).meta_text == "0 courses"


@pytest.mark.unit
def test_clear_courses_state_on_load_error_resets_all_collections() -> None:
    state = CoursesPageState(
        courses=[{"id": 1}],
        tracking_by_course_id={1: {"course_id": 1, "status": "interested"}},
        review_summary_by_course_id={1: {"course_id": 1, "review_count": 1}},
    )
    clear_courses_state_on_load_error(state=state)
    assert state.courses == []
    assert state.tracking_by_course_id == {}
    assert state.review_summary_by_course_id == {}


@pytest.mark.unit
def test_optimistic_tracking_set_and_rollback_restore_previous_state() -> None:
    state = CoursesPageState(tracking_by_course_id={7: {"course_id": 7, "status": "interested"}})
    snap = apply_optimistic_tracking_set(state=state, course_id=7, status="completed")
    assert state.tracking_by_course_id[7]["status"] == "completed"
    rollback_optimistic_tracking(state=state, snapshot=snap)
    assert state.tracking_by_course_id[7]["status"] == "interested"


@pytest.mark.unit
def test_optimistic_tracking_clear_and_rollback_restore_removed_row() -> None:
    state = CoursesPageState(tracking_by_course_id={8: {"course_id": 8, "status": "in_progress"}})
    snap = apply_optimistic_tracking_clear(state=state, course_id=8)
    assert 8 not in state.tracking_by_course_id
    rollback_optimistic_tracking(state=state, snapshot=snap)
    assert state.tracking_by_course_id[8]["status"] == "in_progress"
