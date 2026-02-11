"""Unit tests for pure NiceGUI frontend helpers.

These tests intentionally avoid starting NiceGUI or hitting the backend.
They cover deterministic helper functions which should remain stable as we
refactor UI composition.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from frontend.ui.nicegui.pages import courses as courses_page, home as home_page, my_paths as my_paths_page, paths as paths_page


@pytest.mark.unit
def test_filter_selected_paths_by_needle_and_status() -> None:
    selected = [
        {"id": 1, "name": "Starter", "status": "interested"},
        {"id": 2, "name": "Advanced", "status": "in_progress"},
        {"id": 3, "name": "Data Track", "status": "completed"},
    ]

    assert [p["id"] for p in my_paths_page._filter_selected_paths(selected, needle="ad", status="")] == [2]
    assert [p["id"] for p in my_paths_page._filter_selected_paths(selected, needle="", status="completed")] == [3]
    assert my_paths_page._filter_selected_paths(selected, needle="missing", status="") == []


@pytest.mark.unit
def test_status_label_and_chip_class() -> None:
    assert paths_page._status_label("interested") == "Interested"
    assert paths_page._status_label("in_progress") == "In Progress"
    assert paths_page._status_label("completed") == "Completed"
    assert paths_page._status_label("") == "Not selected"
    assert paths_page._status_label("unknown") == "Not selected"

    assert paths_page._status_chip_class("") == "lp-chip lp-chip--muted"
    assert paths_page._status_chip_class("interested") == "lp-chip lp-chip--sky"
    assert paths_page._status_chip_class("in_progress") == "lp-chip lp-chip--teal"
    assert paths_page._status_chip_class("completed") == "lp-chip lp-chip--lime"


@pytest.mark.unit
def test_home_tracking_map_and_ids_by_status() -> None:
    tracking_rows = [
        {"course_id": 10, "status": "interested"},
        {"course_id": "11", "status": "in_progress"},
        {"course_id": 12, "status": "completed"},
        {"course_id": "bad", "status": "completed"},
    ]
    tracking = home_page._tracking_map(tracking_rows)
    assert tracking == {10: "interested", 11: "in_progress", 12: "completed"}

    interested, in_progress, completed = home_page._ids_by_status(tracking)
    assert interested == [10]
    assert in_progress == [11]
    assert completed == [12]


@pytest.mark.unit
def test_home_recent_tracking_sorts_by_updated_at_desc() -> None:
    rows = [
        {"course_id": 1, "updated_at": "2026-02-01T00:00:00+00:00"},
        {"course_id": 2, "updated_at": "2026-02-03T00:00:00Z"},
        {"course_id": 3, "updated_at": "invalid"},
    ]
    recent = home_page._recent_tracking(rows, limit=2)
    assert [int(r["course_id"]) for r in recent] == [2, 1]


@pytest.mark.unit
def test_home_recent_courses_sorts_by_created_at_desc() -> None:
    courses = [
        {"id": 1, "created_at": "2026-02-01T00:00:00+00:00"},
        {"id": 2, "created_at": "2026-02-02T00:00:00Z"},
        {"id": 3, "created_at": None},
    ]
    recent = home_page._recent_courses(courses, limit=2)
    assert [int(c["id"]) for c in recent] == [2, 1]


@pytest.mark.unit
def test_home_parse_iso_ts_accepts_z() -> None:
    dt = home_page._parse_iso_ts("2026-02-01T12:30:00Z")
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).isoformat().startswith("2026-02-01T12:30:00")


@pytest.mark.unit
def test_course_helpers_are_deterministic() -> None:
    assert courses_page._tracking_label("interested") == "Interested"
    assert courses_page._tracking_label(None) == "Not tracked"

    assert courses_page._tracking_chip_class("in_progress").startswith("lp-chip")
    assert courses_page._parse_duration_hours("1.5") == 1.5
    assert courses_page._parse_duration_hours("bad") is None
