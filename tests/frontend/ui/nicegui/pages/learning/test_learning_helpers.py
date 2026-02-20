"""Unit tests for shared learning helpers (pure functions)."""

from __future__ import annotations

from datetime import timezone

import pytest

from frontend.ui.nicegui.core import datetime_utils
from frontend.ui.nicegui.core.navigation import build_courses_deep_link, build_paths_deep_link
from frontend.ui.nicegui.services.paths_service import compute_path_progress


@pytest.mark.unit
def test_parse_iso_datetime_accepts_z_suffix_and_returns_aware() -> None:
    dt = datetime_utils.parse_iso_datetime("2026-02-01T12:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).isoformat().startswith("2026-02-01T12:30:00")


@pytest.mark.unit
def test_format_date_and_time_are_stable() -> None:
    assert datetime_utils.format_date("2026-02-13T14:49:09+00:00") == "Feb 13, 2026"
    assert datetime_utils.format_time("2026-02-13T14:49:09+00:00").startswith("Feb 13, 2026")
    assert datetime_utils.format_date("bad") == "bad"
    assert datetime_utils.format_time("bad") == "bad"


@pytest.mark.unit
def test_compute_path_progress_handles_empty_courses() -> None:
    completed, total, ratio = compute_path_progress(detail={"courses": []}, tracking_by_course_id={})
    assert completed == 0
    assert total == 0
    assert ratio == 0.0


@pytest.mark.unit
def test_compute_path_progress_counts_completed() -> None:
    detail = {"courses": [{"id": 1}, {"id": 2}, {"id": "bad"}]}
    tracking = {1: {"status": "completed"}, 2: {"status": "in_progress"}}
    completed, total, ratio = compute_path_progress(detail=detail, tracking_by_course_id=tracking)
    assert completed == 1
    assert total == 3
    assert ratio == pytest.approx(1 / 3)


@pytest.mark.unit
def test_learning_navigation_urls_include_id_and_view() -> None:
    assert build_courses_deep_link(course_id=42, view="reviews") == "/courses?tab=tracked&course_id=42&view=reviews"
    assert build_paths_deep_link(path_id=7, view="full") == "/paths?tab=selected&path_id=7&view=full"
