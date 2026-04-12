from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from frontend.ui.nicegui.pages.paths import view_model


@pytest.mark.unit
def test_enrich_path_courses_attaches_reviews_and_tracking_status() -> None:
    courses = [{"id": 10, "title": "HTTP"}, {"id": 11, "title": "FastAPI"}, {"id": "bad", "title": "Ignored"}]
    review_summary = {
        10: {"avg_rating": 4.5, "review_count": 2},
        11: {"avg_rating": 0.0, "review_count": 0},
    }
    tracking = {10: {"status": "in_progress"}}

    out = view_model.enrich_path_courses(
        courses=courses,
        review_summary_by_course_id=review_summary,
        tracking_by_course_id=tracking,
    )

    assert [str(r.get("reviews") or "") for r in out] == ["4.5/5 (2)", "", ""]
    assert [str(r.get("tracking_status") or "") for r in out] == ["in_progress", "", ""]


@pytest.mark.unit
def test_summarize_path_reviews_computes_average_and_count() -> None:
    summary = view_model.summarize_path_reviews(
        path_id=7,
        reviews=[{"rating": 5}, {"rating": "3"}, {"rating": "bad"}],
    )
    assert summary == {"path_id": 7, "avg_rating": 4.0, "review_count": 2}

    empty_summary = view_model.summarize_path_reviews(path_id=7, reviews=[])
    assert empty_summary == {"path_id": 7, "avg_rating": 0.0, "review_count": 0}


@pytest.mark.unit
def test_map_path_card_view_for_tracked_path_includes_progress_and_badges() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "id": 3,
        "created_by": "admin",
        "created_at": (now - timedelta(days=3)).isoformat(),
        "updated_at": (now - timedelta(days=1)).isoformat(),
    }
    detail = {
        "items": [
            {"type": "course", "id": 10, "title": "HTTP"},
            {"type": "course", "id": 11, "title": "FastAPI"},
        ]
    }
    tracking = {10: {"status": "completed"}, 11: {"status": "in_progress"}}
    vm = view_model.map_path_card_view(
        path_row=row,
        is_tracked=True,
        detail=detail,
        tracking_by_course_id=tracking,
        review_summary_row={"avg_rating": 4.5, "review_count": 2},
    )
    assert vm.is_updated is True
    assert vm.is_new is False
    assert vm.rating_badge == "4.5/5 (2)"
    assert vm.completed == 1 and vm.total_courses == 2
    assert vm.milestone in {"Halfway", "Started"}
    assert vm.next_title == "FastAPI"
    assert vm.card_class_suffix == " lp-accent-card--interested"


@pytest.mark.unit
def test_map_path_card_view_for_untracked_path_hides_learning_fields() -> None:
    row = {"id": 7, "created_by": "alice", "created_at": "2026-02-01T00:00:00Z", "updated_at": "2026-02-01T00:00:00Z"}
    vm = view_model.map_path_card_view(
        path_row=row,
        is_tracked=False,
        detail=None,
        tracking_by_course_id={},
        review_summary_row=None,
    )
    assert vm.tracking_label_text == "Not tracked"
    assert vm.completed == 0 and vm.total_courses == 0
    assert vm.milestone == ""
    assert vm.card_class_suffix == ""


@pytest.mark.unit
def test_compute_outcomes_uses_typed_course_items_for_progress_and_next_step() -> None:
    detail = {
        "items": [
            {"type": "video", "id": 9, "title": "Intro"},
            {"type": "course", "id": 10, "title": "HTTP"},
            {"type": "article", "id": 5, "title": "Readme"},
            {"type": "course", "id": 11, "title": "FastAPI"},
        ]
    }
    tracking = {10: {"status": "completed"}, 11: {"status": "in_progress"}}

    out = view_model.compute_outcomes(detail=detail, tracking_by_course_id=tracking)

    assert out["completed"] == 1
    assert out["total"] == 2
    assert out["next_course"] == {"type": "course", "id": 11, "title": "FastAPI"}


@pytest.mark.unit
def test_compute_outcomes_for_learning_item_only_path_uses_reference_copy() -> None:
    detail = {
        "items": [
            {"type": "video", "id": 9, "title": "Intro"},
            {"type": "article", "id": 5, "title": "Readme"},
        ]
    }

    out = view_model.compute_outcomes(detail=detail, tracking_by_course_id={})

    assert out["completed"] == 0
    assert out["total"] == 0
    assert out["milestone"] == "Reference path"
    assert out["impact"] == "Add a course to enable progress tracking."
