from __future__ import annotations

from frontend.ui.nicegui.pages.learning.ui_glue import compute_next_visibility, resolve_tracking_status_value


def test_resolve_tracking_status_value_accepts_direct_value() -> None:
    options = {"": "Not tracked", "completed": "Completed"}
    value = resolve_tracking_status_value(raw_event="completed", options_map=options, fallback_value="")
    assert value == "completed"


def test_resolve_tracking_status_value_accepts_dict_label() -> None:
    options = {"": "Not tracked", "in_progress": "In progress"}
    value = resolve_tracking_status_value(
        raw_event={"label": "In progress"},
        options_map=options,
        fallback_value="",
    )
    assert value == "in_progress"


def test_compute_next_visibility_resets_when_requested() -> None:
    tracked, selected = compute_next_visibility(
        reset_visibility=True,
        page_size=12,
        tracked_visible=48,
        selected_visible=24,
    )
    assert tracked == 12
    assert selected == 12


def test_compute_next_visibility_preserves_when_not_reset() -> None:
    tracked, selected = compute_next_visibility(
        reset_visibility=False,
        page_size=12,
        tracked_visible=48,
        selected_visible=24,
    )
    assert tracked == 48
    assert selected == 24
