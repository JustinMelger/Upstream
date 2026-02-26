"""Focused UI-behavior helper tests for courses/paths pages."""

from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.ui_glue import normalize_course_view_mode
from frontend.ui.nicegui.pages.paths.page import _normalize_path_view_mode, _path_matches_state
from frontend.ui.nicegui.services import paths_service


@pytest.mark.unit
def test_path_tracked_untracked_filter_behavior() -> None:
    selected = {2: {"id": 2}, 5: {"id": 5}}

    assert _path_matches_state(2, selected, "tracked") is True
    assert _path_matches_state(3, selected, "tracked") is False

    assert _path_matches_state(2, selected, "not_tracked") is False
    assert _path_matches_state(3, selected, "not_tracked") is True

    # Empty/unknown filters should not exclude rows.
    assert _path_matches_state(2, selected, "") is True
    assert _path_matches_state(2, selected, "unknown") is True


@pytest.mark.unit
def test_review_only_modal_mode_flags_are_stable() -> None:
    assert normalize_course_view_mode(True) == "reviews"
    assert normalize_course_view_mode(False) == "full"

    assert _normalize_path_view_mode("reviews") == "reviews"
    assert _normalize_path_view_mode("full") == "full"
    assert _normalize_path_view_mode("unexpected") == "full"
    assert _normalize_path_view_mode(None) == "full"


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
        if path == "/paths":
            return [{"id": 42, "name": "P1"}]
        if path == "/paths/selected/list":
            return [{"id": 42, "status": "interested"}]
        if path == "/courses":
            return [{"id": 101, "title": "C1"}]
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


@pytest.mark.unit
@pytest.mark.anyio
async def test_unselect_path_calls_expected_endpoint() -> None:
    api = _FakeApi()
    ok = await paths_service.unselect_path(api=api, path_id=42)
    assert ok is True
    assert api.calls == [("POST", "/paths/42/unselect", {})]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_paths_page_data_returns_expected_shapes() -> None:
    api = _FakeApi()
    paths, selected_by_id, courses, course_by_id = await paths_service.load_paths_page_data(api=api)

    assert isinstance(paths, list) and len(paths) == 1
    assert selected_by_id == {42: {"id": 42, "status": "interested"}}
    assert isinstance(courses, list) and len(courses) == 1
    assert course_by_id == {101: {"id": 101, "title": "C1"}}


class _FakeApiWithDetailFailure:
    async def get(self, path: str, params: dict | None = None):
        if path == "/paths/selected/list":
            return [{"id": 1}, {"id": 2}]
        if path == "/tracking":
            return [{"course_id": 11, "status": "in_progress"}]
        if path == "/paths/1":
            return {"id": 1, "courses": [{"id": 11}]}
        if path == "/paths/2":
            raise RuntimeError("detail failed")
        return {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_my_paths_page_data_tolerates_partial_detail_failures() -> None:
    api = _FakeApiWithDetailFailure()
    selected, details, tracking_by_course_id = await paths_service.load_my_paths_page_data(api=api)

    assert [int(p["id"]) for p in selected] == [1, 2]
    assert details == {1: {"id": 1, "courses": [{"id": 11}]}}
    assert tracking_by_course_id == {11: {"course_id": 11, "status": "in_progress"}}
