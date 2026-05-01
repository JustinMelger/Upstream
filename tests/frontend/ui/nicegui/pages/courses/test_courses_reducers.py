from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.domains.courses.reducers import (
    build_count_options,
    build_status_options,
    compute_facet_counts,
    filter_courses,
    sort_courses,
    tracking_status_key,
)


@pytest.mark.unit
def test_tracking_status_key_defaults_to_not_tracked() -> None:
    tracking = {7: {"status": "interested"}}
    assert tracking_status_key(tracking_by_course_id=tracking, course_id=7) == "interested"
    assert tracking_status_key(tracking_by_course_id=tracking, course_id=8) == "not_tracked"


@pytest.mark.unit
def test_filter_courses_applies_scope_and_filters() -> None:
    courses = [
        {"id": 1, "title": "FastAPI", "description": "Web", "provider": "Docs", "category": "Backend", "level": "Beginner"},
        {"id": 2, "title": "SQL", "description": "DB", "provider": "Docs", "category": "Data", "level": "Beginner"},
        {"id": 3, "title": "HTTP", "description": "Web", "provider": "MDN", "category": "Web", "level": "Intermediate"},
    ]
    tracking = {2: {"status": "completed"}}
    shown = filter_courses(
        courses=courses,
        tracking_by_course_id=tracking,
        scope_value="all",
        needle="web",
        provider_value="",
        category_value="",
        level_value="",
        status_value="",
    )
    assert [int(c["id"]) for c in shown] == [1, 3]

    tracked_only = filter_courses(
        courses=courses,
        tracking_by_course_id=tracking,
        scope_value="tracked",
        needle="",
        provider_value="",
        category_value="",
        level_value="",
        status_value="",
    )
    assert [int(c["id"]) for c in tracked_only] == [2]


@pytest.mark.unit
def test_compute_facet_counts_and_options() -> None:
    courses = [
        {"id": 1, "title": "FastAPI", "description": "Web", "provider": "Docs", "category": "Backend", "level": "Beginner"},
        {"id": 2, "title": "SQL", "description": "DB", "provider": "Docs", "category": "Data", "level": "Beginner"},
        {"id": 3, "title": "HTTP", "description": "Web", "provider": "MDN", "category": "Web", "level": "Intermediate"},
    ]
    tracking = {2: {"status": "completed"}}
    provider_counts, category_counts, level_counts, status_counts = compute_facet_counts(
        courses=courses,
        tracking_by_course_id=tracking,
        scope_value="all",
        needle="",
        provider_value="",
        category_value="",
        level_value="",
        status_value="",
    )
    assert provider_counts["Docs"] == 2
    assert category_counts["Web"] == 1
    assert level_counts["Beginner"] == 2
    assert status_counts["completed"] == 1
    assert status_counts["not_tracked"] == 2

    assert "Docs (2)" in build_count_options(any_label="Any provider", counts=provider_counts).values()
    assert "Completed (1)" in build_status_options(status_counts=status_counts).values()


@pytest.mark.unit
def test_sort_courses_supports_supported_keys() -> None:
    courses = [
        {"id": 1, "title": "B", "created_at": "2026-02-01T00:00:00Z"},
        {"id": 2, "title": "A", "created_at": "2026-02-03T00:00:00Z"},
        {"id": 3, "title": "C", "created_at": "2026-02-02T00:00:00Z"},
    ]
    summaries = {
        1: {"avg_rating": 4.0, "review_count": 2},
        2: {"avg_rating": 4.8, "review_count": 1},
        3: {"avg_rating": 4.8, "review_count": 5},
    }

    newest = sort_courses(
        courses=courses,
        sort_value="newest",
        review_summary_by_course_id=summaries,
        parse_iso_datetime=parse_iso_datetime,
    )
    assert [int(c["id"]) for c in newest] == [2, 3, 1]

    most_reviewed = sort_courses(
        courses=courses,
        sort_value="most_reviewed",
        review_summary_by_course_id=summaries,
        parse_iso_datetime=parse_iso_datetime,
    )
    assert [int(c["id"]) for c in most_reviewed] == [3, 1, 2]
