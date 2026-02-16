"""Focused UI-behavior helper tests for courses/paths pages."""

from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages import courses as courses_page, paths as paths_page


@pytest.mark.unit
def test_path_tracked_untracked_filter_behavior() -> None:
    selected = {2: {"id": 2}, 5: {"id": 5}}

    assert paths_page._path_matches_state(2, selected, "tracked") is True
    assert paths_page._path_matches_state(3, selected, "tracked") is False

    assert paths_page._path_matches_state(2, selected, "not_tracked") is False
    assert paths_page._path_matches_state(3, selected, "not_tracked") is True

    # Empty/unknown filters should not exclude rows.
    assert paths_page._path_matches_state(2, selected, "") is True
    assert paths_page._path_matches_state(2, selected, "unknown") is True


@pytest.mark.unit
def test_review_only_modal_mode_flags_are_stable() -> None:
    assert courses_page._normalize_course_view_mode(True) == "reviews"
    assert courses_page._normalize_course_view_mode(False) == "full"

    assert paths_page._normalize_path_view_mode("reviews") == "reviews"
    assert paths_page._normalize_path_view_mode("full") == "full"
    assert paths_page._normalize_path_view_mode("unexpected") == "full"
    assert paths_page._normalize_path_view_mode(None) == "full"


@pytest.mark.unit
def test_auto_seed_tracking_collects_only_untracked_course_ids() -> None:
    detail = {"courses": [{"id": 10}, {"id": "11"}, {"id": "bad"}, {"foo": "bar"}, 12]}
    tracking = {11: {"status": "completed"}}
    assert paths_page._untracked_path_course_ids(detail, tracking) == [10]

    assert paths_page._untracked_path_course_ids(None, tracking) == []
    assert paths_page._untracked_path_course_ids({"courses": []}, tracking) == []
