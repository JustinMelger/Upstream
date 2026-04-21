from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.pages.paths.reducers import (
    apply_scope_and_status,
    build_status_options,
    compute_status_counts,
    filter_paths_by_needle,
    path_matches_state,
    sort_paths,
)


@pytest.mark.unit
def test_filter_paths_by_needle_matches_name_and_description() -> None:
    rows = [
        {"id": 1, "name": "FastAPI Basics", "description": "API and routing"},
        {"id": 2, "name": "SQL Intro", "description": "Database essentials"},
    ]
    assert [int(r["id"]) for r in filter_paths_by_needle(rows, "fast")] == [1]
    assert [int(r["id"]) for r in filter_paths_by_needle(rows, "database")] == [2]


@pytest.mark.unit
def test_apply_scope_and_status_uses_selected_map_and_status_matcher() -> None:
    rows = [{"id": 1}, {"id": 2}, {"id": 3}]
    selected = {2: {"id": 2}}
    scoped = apply_scope_and_status(
        paths=rows,
        selected_by_id=selected,
        scope_value="selected",
        status_value="",
        path_matches_state=path_matches_state,
    )
    assert [int(r["id"]) for r in scoped] == [2]

    status_filtered = apply_scope_and_status(
        paths=rows,
        selected_by_id=selected,
        scope_value="all",
        status_value="not_tracked",
        path_matches_state=path_matches_state,
    )
    assert [int(r["id"]) for r in status_filtered] == [1, 3]


@pytest.mark.unit
def test_sort_paths_supports_top_rated_most_reviewed_and_name_az() -> None:
    rows = [
        {"id": 1, "name": "B"},
        {"id": 2, "name": "A"},
        {"id": 3, "name": "C"},
    ]
    summaries = {
        1: {"avg_rating": 4.0, "review_count": 2},
        2: {"avg_rating": 4.8, "review_count": 1},
        3: {"avg_rating": 4.8, "review_count": 5},
    }
    top_rated = sort_paths(
        paths=rows,
        sort_value="top_rated",
        path_review_summary_by_id=summaries,
        parse_iso_datetime=parse_iso_datetime,
    )
    assert [int(r["id"]) for r in top_rated] == [3, 2, 1]

    most_reviewed = sort_paths(
        paths=rows,
        sort_value="most_reviewed",
        path_review_summary_by_id=summaries,
        parse_iso_datetime=parse_iso_datetime,
    )
    assert [int(r["id"]) for r in most_reviewed] == [3, 1, 2]

    name_az = sort_paths(
        paths=rows,
        sort_value="name_az",
        path_review_summary_by_id=summaries,
        parse_iso_datetime=parse_iso_datetime,
    )
    assert [int(r["id"]) for r in name_az] == [2, 1, 3]


@pytest.mark.unit
def test_compute_status_counts_and_options() -> None:
    rows = [
        {"id": 1, "name": "FastAPI", "description": ""},
        {"id": 2, "name": "SQL", "description": ""},
        {"id": 3, "name": "HTTP", "description": ""},
    ]
    selected = {2: {"id": 2}}
    counts = compute_status_counts(paths=rows, selected_by_id=selected, scope_value="all", needle="")
    assert counts == {"not_tracked": 2, "tracked": 1}

    options_all = build_status_options(scope_value="all", counts=counts)
    assert "not_tracked" in options_all and "tracked" in options_all

    options_selected = build_status_options(scope_value="selected", counts=counts)
    assert "not_tracked" not in options_selected and "tracked" in options_selected
