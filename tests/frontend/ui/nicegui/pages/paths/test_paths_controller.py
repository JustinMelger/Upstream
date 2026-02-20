from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.state import PathsPageState


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/paths":
            return [{"id": 42, "name": "API Path"}]
        if path == "/paths/selected/list":
            return [{"id": 42, "status": "interested"}]
        if path == "/courses":
            return [{"id": 101, "title": "FastAPI Tutorial"}]
        if path == "/tracking":
            return [{"course_id": 101, "status": "in_progress"}]
        if path == "/paths/42":
            return {"id": 42, "courses": [{"id": 101}, {"id": 102}]}
        if path == "/paths/reviews/summary":
            return [{"path_id": 42, "avg_rating": 4.0, "review_count": 3}]
        if path == "/paths/recommendations/summary":
            return [{"path_id": 42, "recommendation_count": 2}]
        return {}

    async def post(self, path: str, payload: dict | None = None):
        self.calls.append(("POST", path, payload))
        return {"ok": True}

    async def put(self, path: str, payload: dict | None = None):
        self.calls.append(("PUT", path, payload))
        return {"ok": True}

    async def delete(self, path: str):
        self.calls.append(("DELETE", path, None))
        return {"deleted": True}


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_load_all_populates_state() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)
    state = PathsPageState()

    await controller.load_all(state=state)

    assert [int(p["id"]) for p in state.paths] == [42]
    assert state.selected_by_id == {42: {"id": 42, "status": "interested"}}
    assert state.course_by_id == {101: {"id": 101, "title": "FastAPI Tutorial"}}
    assert state.tracking_by_course_id == {101: {"course_id": 101, "status": "in_progress"}}
    assert state.path_review_summary_by_id[42]["review_count"] == 3
    assert state.path_recommendation_summary_by_id[42]["recommendation_count"] == 2


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_select_path_seeds_tracking_and_returns_detail() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)
    state = PathsPageState(tracking_by_course_id={102: {"status": "completed"}})

    seeded, detail = await controller.select_path(path_id=42, state=state)

    assert seeded == 1
    assert isinstance(detail, dict) and int(detail.get("id") or 0) == 42
    assert ("POST", "/paths/42/select", {}) in api.calls
    assert ("POST", "/tracking", {"course_id": 101, "status": "interested"}) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_unselect_path_calls_endpoint() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)

    ok = await controller.unselect_path(path_id=42)
    assert ok is True
    assert ("POST", "/paths/42/unselect", {}) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_load_path_detail_bundle_collects_dialog_payloads() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)

    bundle = await controller.load_path_detail_bundle(path_id=42)

    assert int(bundle.detail.get("id") or 0) == 42
    assert isinstance(bundle.path_reviews, list)
    assert isinstance(bundle.path_recommendations, list)
    assert bundle.course_review_summary_by_course_id == {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_load_path_detail_bundle_tolerates_optional_api_errors() -> None:
    class _ApiWithOptionalFailures(_FakeApi):
        async def get(self, path: str, params: dict | None = None):
            if path in {"/paths/42/reviews", "/paths/42/recommendations", "/courses/reviews/summary"}:
                raise ApiError(status_code=503, message="backend_unreachable")
            return await super().get(path, params=params)

    api = _ApiWithOptionalFailures()
    controller = PathsPageController(api=api)

    bundle = await controller.load_path_detail_bundle(path_id=42)

    assert int(bundle.detail.get("id") or 0) == 42
    assert bundle.path_reviews == []
    assert bundle.path_recommendations == []
    assert bundle.course_review_summary_by_course_id == {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_get_user_recommendation_note_returns_empty_when_missing() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)

    note = await controller.get_user_recommendation_note(path_id=42, username="alice")
    assert note == ""


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_load_recommendation_summary_for_path() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)

    row = await controller.load_recommendation_summary_for_path(path_id=42)
    assert isinstance(row, dict)
    assert int(row.get("recommendation_count") or 0) == 2


@pytest.mark.unit
@pytest.mark.anyio
async def test_controller_path_mutations_call_expected_endpoints() -> None:
    api = _FakeApi()
    controller = PathsPageController(api=api)

    await controller.create_path(payload={"name": "P1", "course_ids": [1]})
    await controller.update_path(path_id=42, payload={"name": "P2", "course_ids": [2]})
    await controller.save_recommendation(path_id=42, note="Great path")
    await controller.save_path_review(path_id=42, rating=5, text="Excellent")
    await controller.delete_path_review(path_id=42, review_id=7)
    await controller.delete_path(path_id=42)

    assert ("POST", "/paths", {"name": "P1", "course_ids": [1]}) in api.calls
    assert ("PUT", "/paths/42", {"name": "P2", "course_ids": [2]}) in api.calls
    assert ("POST", "/paths/42/recommendations", {"note": "Great path"}) in api.calls
    assert ("POST", "/paths/42/reviews", {"rating": 5, "text": "Excellent"}) in api.calls
    assert ("DELETE", "/paths/42/reviews/7", None) in api.calls
    assert ("DELETE", "/paths/42", None) in api.calls
