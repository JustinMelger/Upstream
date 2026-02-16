"""Focused UI-behavior helper tests for courses/paths pages."""

from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages import courses as courses_page, paths as paths_page
from frontend.ui.nicegui.services import paths_service


@pytest.mark.unit
def test_path_tracked_untracked_filter_behavior() -> None:
    selected = {2: {"id": 2}, 5: {"id": 5}}

    assert paths_page._path_matches_state(2, selected, "tracked") is True
    assert paths_page._path_matches_state(3, selected, "tracked") is False

    assert paths_page._path_matches_state(2, selected, "not_tracked") is False
    assert paths_page._path_matches_state(3, selected, "not_tracked") is True

    # Empty/unknown filters should not exclude rows.
    assert paths_page._path_matches_state(2, selected, "") is True
    assert paths_page._path_matches_state(2, selected, "unknown") is True


@pytest.mark.unit
def test_review_only_modal_mode_flags_are_stable() -> None:
    assert courses_page._normalize_course_view_mode(True) == "reviews"
    assert courses_page._normalize_course_view_mode(False) == "full"

    assert paths_page._normalize_path_view_mode("reviews") == "reviews"
    assert paths_page._normalize_path_view_mode("full") == "full"
    assert paths_page._normalize_path_view_mode("unexpected") == "full"
    assert paths_page._normalize_path_view_mode(None) == "full"


@pytest.mark.unit
def test_auto_seed_tracking_collects_only_untracked_course_ids() -> None:
    detail = {"courses": [{"id": 10}, {"id": "11"}, {"id": "bad"}, {"foo": "bar"}, 12]}
    tracking = {11: {"status": "completed"}}
    assert paths_service.untracked_path_course_ids(detail=detail, tracking_by_course_id=tracking) == [10]

    assert paths_service.untracked_path_course_ids(detail=None, tracking_by_course_id=tracking) == []
    assert paths_service.untracked_path_course_ids(detail={"courses": []}, tracking_by_course_id=tracking) == []


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def post(self, path: str, payload: dict | None = None):
        self.calls.append(("POST", path, payload))
        return {"ok": True}

    async def get(self, path: str):
        self.calls.append(("GET", path, None))
        if path == "/paths/42":
            return {"id": 42, "courses": [{"id": 101}, {"id": 102}]}
        return {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_select_path_and_seed_tracking_calls_expected_endpoints() -> None:
    api = _FakeApi()
    seeded, detail = await paths_service.select_path_and_seed_tracking(
        api=api,
        path_id=42,
        tracking_by_course_id={102: {"status": "completed"}},
    )
    assert seeded == 1
    assert isinstance(detail, dict) and int(detail.get("id") or 0) == 42
    assert api.calls[0] == ("POST", "/paths/42/select", {})
    assert api.calls[1] == ("GET", "/paths/42", None)
    assert ("POST", "/tracking", {"course_id": 101, "status": "interested"}) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_select_path_and_seed_tracking_uses_cached_detail() -> None:
    api = _FakeApi()
    seeded, detail = await paths_service.select_path_and_seed_tracking(
        api=api,
        path_id=42,
        tracking_by_course_id={101: {"status": "in_progress"}, 102: {"status": "completed"}},
        cached_detail={"id": 42, "courses": [{"id": 101}, {"id": 102}]},
    )
    assert seeded == 0
    assert isinstance(detail, dict) and int(detail.get("id") or 0) == 42
    assert api.calls == [("POST", "/paths/42/select", {})]
