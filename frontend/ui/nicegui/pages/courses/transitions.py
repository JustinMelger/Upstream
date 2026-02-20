"""Pure state-transition helpers for Courses page."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.courses.state import CoursesPageState


@dataclass(slots=True)
class LoadTransition:
    """UI transition payload for page loading lifecycle."""

    loading: bool
    visible_count: int
    meta_text: str
    loaded_once: bool


@dataclass(slots=True)
class TrackingSnapshot:
    """Snapshot used for optimistic tracking rollback."""

    course_id: int
    had_row: bool
    row: dict[str, Any] | None


def begin_courses_load(*, page_size: int) -> LoadTransition:
    """Transition payload for load-start."""
    return LoadTransition(loading=True, visible_count=int(page_size), meta_text="Loading...", loaded_once=False)


def complete_courses_load(*, course_count: int) -> LoadTransition:
    """Transition payload for successful load completion."""
    return LoadTransition(loading=False, visible_count=0, meta_text=f"{int(course_count)} courses", loaded_once=True)


def fail_courses_load() -> LoadTransition:
    """Transition payload for failed load completion."""
    return LoadTransition(loading=False, visible_count=0, meta_text="0 courses", loaded_once=True)


def finalize_courses_load(*, ok: bool, course_count: int) -> LoadTransition:
    """Return final load transition based on success/failure outcome."""
    return complete_courses_load(course_count=course_count) if bool(ok) else fail_courses_load()


def clear_courses_state_on_load_error(*, state: CoursesPageState) -> None:
    """Reset course page state on list-load error."""
    state.courses = []
    state.tracking_by_course_id = {}
    state.review_summary_by_course_id = {}
    state.recommendation_summary_by_course_id = {}


def apply_optimistic_tracking_set(*, state: CoursesPageState, course_id: int, status: str) -> TrackingSnapshot:
    """Optimistically set tracking status and return rollback snapshot."""
    cid = int(course_id)
    current = state.tracking_by_course_id.get(cid)
    snapshot = TrackingSnapshot(
        course_id=cid,
        had_row=cid in state.tracking_by_course_id,
        row=deepcopy(current) if isinstance(current, dict) else None,
    )
    state.tracking_by_course_id[cid] = {"course_id": cid, "status": str(status or "").strip()}
    return snapshot


def apply_optimistic_tracking_clear(*, state: CoursesPageState, course_id: int) -> TrackingSnapshot:
    """Optimistically clear tracking status and return rollback snapshot."""
    cid = int(course_id)
    current = state.tracking_by_course_id.get(cid)
    snapshot = TrackingSnapshot(
        course_id=cid,
        had_row=cid in state.tracking_by_course_id,
        row=deepcopy(current) if isinstance(current, dict) else None,
    )
    state.tracking_by_course_id.pop(cid, None)
    return snapshot


def rollback_optimistic_tracking(*, state: CoursesPageState, snapshot: TrackingSnapshot) -> None:
    """Rollback optimistic tracking mutation from snapshot."""
    cid = int(snapshot.course_id)
    if snapshot.had_row and isinstance(snapshot.row, dict):
        state.tracking_by_course_id[cid] = deepcopy(snapshot.row)
    elif not snapshot.had_row:
        state.tracking_by_course_id.pop(cid, None)
