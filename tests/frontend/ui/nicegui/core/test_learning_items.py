from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.learning_items import (
    infer_learning_item_type,
    interleave_learning_item_entries,
    learning_item_capabilities,
    learning_item_primary_action_label,
    learning_item_review_action_label,
    learning_item_source_action_label,
    learning_item_type_label,
    normalize_learning_item_type,
)


@pytest.mark.unit
def test_infer_learning_item_type_distinguishes_video_course_and_article() -> None:
    assert infer_learning_item_type(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "video"
    assert infer_learning_item_type(url="https://www.udemy.com/course/fastapi-zero-to-prod/") == "course"
    assert infer_learning_item_type(url="https://fastapi.tiangolo.com/tutorial/testing/") == "article"


@pytest.mark.unit
def test_infer_learning_item_type_uses_provider_hints_when_url_is_generic() -> None:
    assert infer_learning_item_type(url="https://example.com/watch", provider="YouTube") == "video"
    assert infer_learning_item_type(url="https://example.com/learn", provider="Udemy") == "course"
    assert infer_learning_item_type(url="https://example.com/post", provider="Independent Blog") == "article"


@pytest.mark.unit
def test_interleave_learning_item_entries_preserves_subtype_diversity() -> None:
    ordered = interleave_learning_item_entries(
        entries=[
            {"learning_item_type": "course", "id": 1},
            {"learning_item_type": "course", "id": 2},
            {"learning_item_type": "video", "id": 3},
            {"learning_item_type": "article", "id": 4},
            {"learning_item_type": "course", "id": 5},
        ]
    )
    assert [entry["id"] for entry in ordered[:4]] == [3, 1, 4, 2]


@pytest.mark.unit
def test_learning_item_helpers_normalize_and_label_supported_types() -> None:
    assert normalize_learning_item_type("VIDEO") == "video"
    assert normalize_learning_item_type("unknown", default="article") == "article"
    assert learning_item_type_label("course") == "Course"
    assert learning_item_primary_action_label("video") == "Watch video"
    assert learning_item_primary_action_label("article") == "Read article"
    assert learning_item_review_action_label("video") == "Review video"
    assert learning_item_review_action_label("course") == "Review course"
    assert learning_item_review_action_label("article") == "Review article"
    assert learning_item_source_action_label("course") == "Open course source"
    assert learning_item_source_action_label("video") == "Open video source"


@pytest.mark.unit
def test_learning_item_capabilities_match_current_product_model() -> None:
    course = learning_item_capabilities("course")
    article = learning_item_capabilities("article")
    video = learning_item_capabilities("video")

    assert course.supports_tracking is True
    assert course.supports_reviews is True
    assert course.supports_recommendations is True
    assert article.supports_tracking is False
    assert article.supports_reviews is True
    assert article.supports_recommendations is False
    assert video.supports_tracking is False
    assert video.supports_reviews is True
    assert video.supports_recommendations is False
