"""Unit tests for the learning service layer (mocked ApiClient)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

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
