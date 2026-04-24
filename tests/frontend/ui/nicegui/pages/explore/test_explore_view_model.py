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

    assert [item.learning_item_type for item in results.shown_learning_items] == ["course", "article", "course"]
    assert [item.id for item in results.shown_learning_items] == [1, 11, 2]


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
    assert "course" in default_slice_types
    assert "article" in default_slice_types


@pytest.mark.unit
def test_build_explore_visible_results_surfaces_real_video_rows_ahead_of_courses_in_default_slice() -> None:
    state = ExplorePageState(
        courses=[
            {
                "id": index,
                "title": f"Course {index}",
                "url": f"https://www.udemy.com/course/course-{index}/",
                "provider": "Udemy",
            }
            for index in range(1, 9)
        ],
        videos=[
            {
                "id": 40,
                "title": "Team walkthrough",
                "url": "https://www.youtube.com/watch?v=team-walkthrough",
                "provider": "YouTube",
                "created_at": "2026-04-19T10:00:00Z",
            }
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
    default_slice_ids = [item.id for item in results.shown_learning_items[:8]]
    assert "video" in default_slice_types
    assert 40 in default_slice_ids


@pytest.mark.unit
def test_build_explore_visible_results_preserves_default_video_order_for_new_shares() -> None:
    state = ExplorePageState(
        videos=[
            {
                "id": 40,
                "title": "Zebra walkthrough",
                "url": "https://www.youtube.com/watch?v=zebra",
                "provider": "YouTube",
                "created_at": "2026-04-19T10:00:00Z",
            },
            {
                "id": 12,
                "title": "Alpha intro",
                "url": "https://www.youtube.com/watch?v=alpha",
                "provider": "YouTube",
                "created_at": "2026-04-18T10:00:00Z",
            },
        ]
    )

    results = build_explore_visible_results(state=state, filters=ExploreListFilters())

    assert [item.id for item in results.shown_learning_items] == [40, 12]
