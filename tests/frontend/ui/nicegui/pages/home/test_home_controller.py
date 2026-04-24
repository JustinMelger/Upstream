from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.shared_stats.controller import SharedStatsController


@pytest.mark.unit
@pytest.mark.anyio
async def test_home_controller_load_overview_for_user_uses_colleague_stats() -> None:
    calls: list[tuple[str, dict | None]] = []

    class _Api:
        async def get(self, path: str, params: dict | None = None):  # noqa: ANN001
            calls.append((path, params))
            if path == "/tracking/stats" and params is None:
                return {"interested": 99}
            return {"interested": 3, "in_progress": 2, "completed": 1}

    c = SharedStatsController(api=_Api())  # type: ignore[arg-type]
    out = await c.load_overview(username="bob", is_admin=False, mode_value="mine")
    assert out.snapshot_stats == {"interested": 3, "in_progress": 2, "completed": 1}
    assert out.team_stats_by_user == []
    assert calls == [("/tracking/stats", {"colleague_id": "bob"})]


@pytest.mark.unit
@pytest.mark.anyio
async def test_home_controller_load_overview_for_admin_team_uses_team_endpoints() -> None:
    calls: list[tuple[str, dict | None]] = []

    class _Api:
        async def get(self, path: str, params: dict | None = None):  # noqa: ANN001
            calls.append((path, params))
            if path == "/tracking/stats/users":
                return [{"colleague_id": "alice", "completed": 2}]
            return {"interested": 10, "in_progress": 4, "completed": 6}

    c = SharedStatsController(api=_Api())  # type: ignore[arg-type]
    out = await c.load_overview(username="admin", is_admin=True, mode_value="team")
    assert out.snapshot_stats == {"interested": 10, "in_progress": 4, "completed": 6}
    assert out.team_stats_by_user == [{"colleague_id": "alice", "completed": 2}]
    assert len(calls) == 2
    assert set(calls) == {("/tracking/stats", None), ("/tracking/stats/users", None)}
