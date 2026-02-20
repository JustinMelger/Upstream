"""Unit tests for the learning service layer (mocked ApiClient)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.services.learning_service import (
    clear_tracking_status,
    load_my_learning_data,
    save_recommended_course,
    save_recommended_path,
    set_tracking_status,
)


@dataclass(slots=True)
class _FakeApi:
    """Minimal fake ApiClient for service tests."""

    payloads: dict[str, Any]

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:  # noqa: ARG002
        return self.payloads.get(path)

    async def post(self, _path: str, _payload: dict[str, Any]) -> Any:
        return {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_my_learning_data_slices_tracked_selected_and_shared() -> None:
    api = _FakeApi(
        payloads={
            "/courses": [
                {"id": 1, "title": "C1", "created_by": "alice"},
                {"id": 2, "title": "C2", "created_by": "bob"},
            ],
            "/tracking": [{"course_id": 2, "status": "in_progress"}],
            "/paths": [
                {"id": 10, "name": "P1", "created_by": "alice"},
                {"id": 11, "name": "P2", "created_by": "bob"},
            ],
            "/paths/selected/list": [{"id": 11, "name": "P2", "status": "interested"}],
            "/paths/11": {"id": 11, "name": "P2", "courses": [{"id": 2}]},
            "/articles": [{"id": 100, "title": "A1", "created_by": "alice"}],
        }
    )

    data = await load_my_learning_data(api=api, username="alice", include_articles=True)
    assert [int(c["id"]) for c in data["tracked_courses"]] == [2]
    assert [int(p["id"]) for p in data["selected_paths"]] == [11]
    assert int(data["path_details_by_id"][11]["id"]) == 11
    assert [int(c["id"]) for c in data["shared_courses"]] == [1]
    assert [int(p["id"]) for p in data["shared_paths"]] == [10]
    assert [int(a["id"]) for a in data["shared_articles"]] == [100]


@pytest.mark.unit
@pytest.mark.anyio
async def test_learning_tracking_mutation_use_cases_call_expected_endpoints() -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class _Api:
        async def post(self, path: str, payload: dict[str, Any]) -> Any:
            calls.append((path, payload))
            return {}

    api = _Api()
    await set_tracking_status(api=api, course_id=3, status="in_progress")
    await clear_tracking_status(api=api, course_id=3)
    await save_recommended_course(api=api, course_id=9)
    await save_recommended_path(api=api, path_id=4)

    assert calls == [
        ("/tracking", {"course_id": 3, "status": "in_progress"}),
        ("/tracking/delete", {"course_id": 3}),
        ("/tracking", {"course_id": 9, "status": "interested"}),
        ("/paths/4/select", {}),
    ]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_my_learning_data_keeps_working_when_summary_endpoints_fail_with_api_error() -> None:
    class _Api(_FakeApi):
        async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:  # noqa: ARG002
            if path in {
                "/courses/reviews/summary",
                "/paths/reviews/summary",
                "/courses/recommendations/summary",
                "/paths/recommendations/summary",
            }:
                raise ApiError(status_code=503, message="backend_unreachable")
            return self.payloads.get(path)

    api = _Api(
        payloads={
            "/courses": [{"id": 2, "title": "C2", "created_by": "bob"}],
            "/tracking": [{"course_id": 2, "status": "in_progress"}],
            "/paths": [{"id": 11, "name": "P2", "created_by": "bob"}],
            "/paths/selected/list": [{"id": 11, "name": "P2", "status": "interested"}],
            "/paths/11": {"id": 11, "name": "P2", "courses": [{"id": 2}]},
            "/articles": [],
            "/courses/2/reviews": [],
            "/paths/11/reviews": [],
        }
    )

    data = await load_my_learning_data(api=api, username="alice", include_articles=True)
    assert data["course_review_summary_by_id"] == {}
    assert data["path_review_summary_by_id"] == {}
    assert data["course_recommendation_summary_by_id"] == {}
    assert data["path_recommendation_summary_by_id"] == {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_my_learning_data_does_not_swallow_unexpected_summary_errors() -> None:
    class _Api(_FakeApi):
        async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:  # noqa: ARG002
            if path == "/courses/reviews/summary":
                raise RuntimeError("boom")
            return self.payloads.get(path)

    api = _Api(
        payloads={
            "/courses": [{"id": 2, "title": "C2", "created_by": "bob"}],
            "/tracking": [{"course_id": 2, "status": "in_progress"}],
            "/paths": [],
            "/paths/selected/list": [],
            "/articles": [],
            "/courses/2/reviews": [],
        }
    )

    with pytest.raises(RuntimeError, match="boom"):
        await load_my_learning_data(api=api, username="alice", include_articles=True)
