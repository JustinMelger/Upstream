from __future__ import annotations

import pytest

from frontend.ui.nicegui.services import paths_service


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def post(self, path: str, payload: dict | None = None):
        self.calls.append(("POST", path, payload))
        if payload and int(payload.get("course_id") or 0) == 102:
            raise RuntimeError("seed failed")
        return {"ok": True}

    async def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/paths/7":
            return {
                "id": 7,
                "items": [
                    {"type": "course", "id": 101},
                    {"type": "course", "id": 102},
                ],
            }
        if path == "/paths/selected/list":
            return [{"id": 7}, {"id": "bad"}]
        if path == "/tracking":
            return [{"course_id": 101, "status": "completed"}]
        return []


@pytest.mark.unit
@pytest.mark.anyio
async def test_select_path_and_seed_tracking_counts_only_successful_seed_posts() -> None:
    api = _FakeApi()
    seeded, detail = await paths_service.select_path_and_seed_tracking(
        api=api,
        path_id=7,
        tracking_by_course_id={},
    )
    # 101 succeeds, 102 raises and is ignored by gather(return_exceptions=True)
    assert seeded == 1
    assert isinstance(detail, dict) and int(detail.get("id") or 0) == 7
    assert ("POST", "/paths/7/select", {}) in api.calls
    assert ("GET", "/paths/7", None) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_my_paths_page_data_ignores_invalid_selected_ids() -> None:
    api = _FakeApi()
    selected, details, tracking = await paths_service.load_my_paths_page_data(api=api)
    assert [int(row["id"]) for row in selected if str(row.get("id")).isdigit()] == [7]
    assert set(details.keys()) == {7}
    assert tracking == {101: {"course_id": 101, "status": "completed"}}
