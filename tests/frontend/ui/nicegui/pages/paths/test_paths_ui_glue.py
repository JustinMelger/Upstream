from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths.ui_glue import collect_active_filter_chips, next_visible_count


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
def test_next_visible_count_caps_at_total() -> None:
    assert next_visible_count(current=10, total=25, page_size=10) == 20
    assert next_visible_count(current=20, total=25, page_size=10) == 25
