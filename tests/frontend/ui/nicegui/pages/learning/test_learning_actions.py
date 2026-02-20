from __future__ import annotations

from frontend.ui.nicegui.pages.learning.actions import (
    dismiss_recommended_course,
    dismiss_recommended_path,
    load_more_selected,
    load_more_tracked,
)
from frontend.ui.nicegui.pages.learning.state import LearningPageState


def test_dismiss_recommended_course_and_path_refreshes() -> None:
    state = LearningPageState()
    refresh_calls = {"count": 0}

    def _refresh() -> None:
        refresh_calls["count"] += 1

    dismiss_recommended_course(state=state, course_id=7, refresh=_refresh)
    dismiss_recommended_path(state=state, path_id=3, refresh=_refresh)

    assert state.dismissed_recommended_course_ids == {7}
    assert state.dismissed_recommended_path_ids == {3}
    assert refresh_calls["count"] == 2


def test_load_more_handlers_cap_visibility_and_refresh() -> None:
    state = LearningPageState(page_size=10, tracked_visible=10, selected_visible=20)
    refresh_calls = {"count": 0}

    def _refresh() -> None:
        refresh_calls["count"] += 1

    load_more_tracked(state=state, total_count=25, refresh=_refresh)
    load_more_selected(state=state, total_count=22, refresh=_refresh)

    assert state.tracked_visible == 20
    assert state.selected_visible == 22
    assert refresh_calls["count"] == 2
