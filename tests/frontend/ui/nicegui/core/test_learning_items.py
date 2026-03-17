from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.learning_items import (
    infer_learning_item_type,
    interleave_learning_item_entries,
    learning_item_type_label,
    normalize_learning_item_type,
)


@pytest.mark.unit
def test_infer_learning_item_type_distinguishes_video_course_and_article() -> None:
    assert infer_learning_item_type(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "video"
    assert infer_learning_item_type(url="https://www.udemy.com/course/fastapi-zero-to-prod/") == "course"
    assert infer_learning_item_type(url="https://fastapi.tiangolo.com/tutorial/testing/") == "article"


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
