from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses import view_model


@pytest.mark.unit
def test_course_badge_formatters() -> None:
    assert view_model.format_rating_badge({"avg_rating": 4.5, "review_count": 2}) == "★ 4.5 (2)"
    assert view_model.format_rating_badge({"avg_rating": 4.5, "review_count": 0}) == ""
    assert view_model.format_recommendation_badge({"recommendation_count": 3}) == "↗ 3 rec"
    assert view_model.format_recommendation_badge({"recommendation_count": 0}) == ""


@pytest.mark.unit
def test_map_course_card_view_for_tracked_updated_course() -> None:
    row = {
        "id": 5,
        "created_by": "admin",
        "created_at": "2026-02-18T00:00:00Z",
        "updated_at": "2026-02-20T00:00:00Z",
    }
    tracked = {"status": "in_progress"}
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=tracked,
        review_summary_row={"avg_rating": 4.7, "review_count": 3},
        recommendation_summary_row={"recommendation_count": 2},
    )
    assert vm.is_updated is True
    assert vm.is_new is False
    assert vm.card_class_suffix == " lp-course-card--in_progress"
    assert vm.shared_by == "admin"
    assert vm.rating_badge == "★ 4.7 (3)"
    assert vm.recommendation_badge == "↗ 2 rec"
    assert vm.tracking_label_text == "In Progress"
    assert vm.tracking_chip_cls.startswith("lp-chip")


@pytest.mark.unit
def test_map_course_card_view_for_untracked_course() -> None:
    row = {"id": 7, "created_by": "alice", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=None,
        review_summary_row=None,
        recommendation_summary_row=None,
    )
    assert vm.card_class_suffix == ""
    assert vm.rating_badge == ""
    assert vm.recommendation_badge == ""
    assert vm.tracking_label_text == "Not tracked"
