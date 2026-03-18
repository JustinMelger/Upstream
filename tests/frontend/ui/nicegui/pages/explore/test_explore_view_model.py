from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.explore.view_model import build_explore_visible_results, ExploreListFilters


@pytest.mark.unit
def test_build_explore_visible_results_interleaves_learning_item_subtypes() -> None:
    state = ExplorePageState(
        courses=[
            {
                "id": 1,
                "title": "Udemy FastAPI",
                "url": "https://www.udemy.com/course/fastapi-zero-to-prod/",
                "provider": "Udemy",
            },
            {
                "id": 2,
                "title": "YouTube Async Python",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "provider": "YouTube",
            },
        ],
        articles=[
            {
                "id": 11,
                "title": "FastAPI Testing",
                "url": "https://fastapi.tiangolo.com/tutorial/testing/",
                "tags": "fastapi,testing",
            }
        ],
    )

    results = build_explore_visible_results(state=state, filters=ExploreListFilters())

    assert [item.learning_item_type for item in results.shown_learning_items] == ["video", "course", "article"]
    assert [item.id for item in results.shown_learning_items] == [2, 1, 11]


@pytest.mark.unit
def test_build_explore_visible_results_keeps_all_available_subtypes_visible_in_default_slice() -> None:
    state = ExplorePageState(
        courses=[
            {
                "id": 1,
                "title": "YouTube Async Python",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "provider": "YouTube",
            },
            *[
                {
                    "id": index,
                    "title": f"Udemy Course {index}",
                    "url": f"https://www.udemy.com/course/course-{index}/",
                    "provider": "Udemy",
                }
                for index in range(2, 10)
            ],
        ],
        articles=[
            {
                "id": 21,
                "title": "FastAPI Testing",
                "url": "https://fastapi.tiangolo.com/tutorial/testing/",
                "tags": "fastapi,testing",
            }
        ],
    )

    results = build_explore_visible_results(state=state, filters=ExploreListFilters())

    default_slice_types = [item.learning_item_type for item in results.shown_learning_items[:8]]
    assert "video" in default_slice_types
    assert "course" in default_slice_types
    assert "article" in default_slice_types
