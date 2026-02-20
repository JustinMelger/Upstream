from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths.ui_glue import (
    collect_active_filter_chips,
    compute_expanded_visible_count,
    compute_paths_meta_text,
)


@pytest.mark.unit
def test_collect_active_filter_chips_builds_expected_labels() -> None:
    chips = collect_active_filter_chips(
        scope_value="selected",
        search_value="api",
        status_value="tracked",
        sort_value="newest",
        status_options={"tracked": "Tracked (2)"},
        sort_options={"newest": "Newest"},
    )
    assert [(c.key, c.label) for c in chips] == [
        ("scope", "View: Selected"),
        ("search", "Search: api"),
        ("status", "Status: Tracked (2)"),
        ("sort", "Sort: Newest"),
    ]


@pytest.mark.unit
def test_collect_active_filter_chips_empty_when_no_filters() -> None:
    chips = collect_active_filter_chips(
        scope_value="all",
        search_value="",
        status_value="",
        sort_value="",
        status_options={},
        sort_options={},
    )
    assert chips == []


@pytest.mark.unit
def test_compute_paths_meta_text() -> None:
    assert compute_paths_meta_text(path_count=0) == "0 paths"
    assert compute_paths_meta_text(path_count=8) == "8 paths"


@pytest.mark.unit
def test_compute_expanded_visible_count_caps_at_total() -> None:
    assert compute_expanded_visible_count(current_visible=10, total_count=25, page_size=10) == 20
    assert compute_expanded_visible_count(current_visible=20, total_count=25, page_size=10) == 25
