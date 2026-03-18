from __future__ import annotations

from frontend.ui.nicegui.pages.learning.view_model import (
    build_learning_tab_view,
    build_recently_shared_in_teams,
    build_shared_tab_view,
)


def test_build_shared_tab_view_projects_expected_fields() -> None:
    data = {
        "shared_courses": [{"id": 1, "title": "Udemy course", "url": "https://www.udemy.com/course/test/", "provider": "Udemy"}],
        "shared_videos": [{"id": 4, "title": "Video title", "url": "https://youtu.be/demo"}],
        "shared_paths": [{"id": 2}],
        "shared_articles": [{"id": 3, "title": "Article title"}],
        "shared_course_review_summary_by_id": {1: {"review_count": 2}},
        "shared_course_recommendation_summary_by_id": {1: {"recommendation_count": 1}},
        "shared_path_review_summary_by_id": {2: {"review_count": 3}},
        "shared_path_recommendation_summary_by_id": {2: {"recommendation_count": 4}},
    }
    vm = build_shared_tab_view(data=data)
    assert [int(c["id"]) for c in vm.shared_courses] == [1]
    assert [int(p["id"]) for p in vm.shared_paths] == [2]
    assert [int(a["id"]) for a in vm.shared_articles] == [3]
    assert [(item.item_type, item.item_id) for item in vm.shared_learning_items] == [("article", 3), ("course", 1), ("video", 4)]
    assert int((vm.shared_learning_items[1].review_summary_row or {})["review_count"]) == 2
    assert vm.shared_learning_items[0].capabilities.supports_reviews is True
    assert vm.shared_learning_items[2].capabilities.supports_reviews is False
    assert int(vm.shared_path_recommendation_summary_by_id[2]["recommendation_count"]) == 4


def test_build_learning_tab_view_filters_dismissed_recommendations_and_sorts_pending_ids() -> None:
    data = {
        "tracked_courses": [{"id": 10}],
        "tracking_by_course_id": {10: {"status": "in_progress"}},
        "selected_paths": [{"id": 20}],
        "path_details_by_id": {20: {"id": 20, "courses": [{"id": 10}]}},
        "course_review_summary_by_id": {10: {"review_count": 2}},
        "path_review_summary_by_id": {20: {"review_count": 1}},
        "pending_course_review_ids": ["7", 3, 7],
        "pending_path_review_ids": [9, "2", 9],
        "recommended_courses_for_you": [{"course_id": 1}, {"course_id": 2}, {"course_id": 0}, "bad"],
        "recommended_paths_for_you": [{"path_id": 3}, {"path_id": 4}, {"path_id": 0}, "bad"],
    }
    vm = build_learning_tab_view(
        data=data,
        dismissed_recommended_course_ids={2},
        dismissed_recommended_path_ids={4},
    )
    assert [int(c["id"]) for c in vm.tracked_courses] == [10]
    assert vm.pending_course_review_ids == [3, 7]
    assert vm.pending_path_review_ids == [2, 9]
    assert [int(r["course_id"]) for r in vm.recommended_courses] == [1]
    assert [int(r["path_id"]) for r in vm.recommended_paths] == [3]


def test_build_learning_tab_view_ignores_invalid_pending_review_ids() -> None:
    vm = build_learning_tab_view(
        data={
            "pending_course_review_ids": ["bad", None, "", 0, -1, "5"],
            "pending_path_review_ids": ["x", 3.0, "0"],
        },
        dismissed_recommended_course_ids=set(),
        dismissed_recommended_path_ids=set(),
    )
    assert vm.pending_course_review_ids == [5]
    assert vm.pending_path_review_ids == [3]


def test_build_recently_shared_in_teams_excludes_current_user_and_sorts() -> None:
    items = build_recently_shared_in_teams(
        data={
            "courses": [
                {"id": 1, "title": "A", "created_by": "alice", "updated_at": "2026-02-20T10:00:00Z"},
                {"id": 2, "title": "Mine", "created_by": "bob", "updated_at": "2026-02-24T10:00:00Z"},
            ],
            "videos": [{"id": 50, "title": "Video 1", "created_by": "erin", "updated_at": "2026-02-23T10:00:00Z"}],
            "paths": [{"id": 10, "name": "Path 1", "created_by": "charlie", "updated_at": "2026-02-21T10:00:00Z"}],
            "articles": [{"id": 100, "title": "Article 1", "created_by": "dana", "updated_at": "2026-02-22T10:00:00Z"}],
        },
        username="bob",
        limit=4,
    )
    assert [(str(i["type"]), int(i["id"])) for i in items] == [
        ("video", 50),
        ("article", 100),
        ("path", 10),
        ("course", 1),
    ]
