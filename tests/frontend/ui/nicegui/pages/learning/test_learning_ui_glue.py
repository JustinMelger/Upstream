from __future__ import annotations

from frontend.ui.nicegui.pages.learning.ui_glue import (
    compute_expanded_visible_count,
    compute_meta_text,
    compute_next_visibility,
    resolve_tracking_status_value,
)


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


def test_compute_meta_text_for_shared_and_learning_views() -> None:
    data = {
        "shared_courses": [{"id": 1}],
        "shared_videos": [{"id": 4}],
        "shared_paths": [{"id": 2}],
        "shared_articles": [{"id": 3}],
        "tracked_courses": [{"id": 10}, {"id": 11}],
        "selected_paths": [{"id": 20}],
    }
    assert compute_meta_text(data=data, view="shared", feature_articles=True) == "3 learning items · 1 path"
    assert compute_meta_text(data=data, view="shared", feature_articles=False) == "2 learning items · 1 path"
    assert compute_meta_text(data=data, view="learning", feature_articles=True) == "2 tracked courses · 1 selected paths"


def test_compute_expanded_visible_count_caps_at_total() -> None:
    assert compute_expanded_visible_count(current_visible=10, total_count=22, page_size=5) == 15
    assert compute_expanded_visible_count(current_visible=20, total_count=22, page_size=5) == 22
