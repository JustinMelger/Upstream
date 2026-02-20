from __future__ import annotations

from typing import Any

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.services.dashboard_service import load_dashboard_data


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self.calls.append((path, params))
        if path == "/courses":
            return [{"id": 5, "title": "C5"}]
        if path == "/paths":
            return [{"id": 7, "name": "P7"}]
        if path == "/paths/selected/list":
            return [{"id": 7, "name": "P7"}]
        if path == "/tracking":
            return [{"course_id": 5, "status": "in_progress"}]
        if path == "/tracking/stats":
            return {"tracked": 1}
        if path == "/courses/reviews/summary":
            raise ApiError(status_code=503, message="backend_unreachable")
        if path == "/paths/7":
            raise ApiError(status_code=404, message="not_found")
        return []


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_dashboard_data_tolerates_optional_summary_and_detail_api_errors() -> None:
    api = _FakeApi()

    data = await load_dashboard_data(
        api=api,
        username="alice",
        is_admin=False,
        mode_value="mine",
    )

    assert data.snapshot_stats == {"tracked": 1}
    assert data.review_summary_by_course_id == {}
    assert data.selected_path_details == []
