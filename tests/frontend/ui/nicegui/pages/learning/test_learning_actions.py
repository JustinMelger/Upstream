from __future__ import annotations

from frontend.ui.nicegui.pages.learning.actions import load_more_selected, load_more_tracked
from frontend.ui.nicegui.pages.learning.state import LearningPageState


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
