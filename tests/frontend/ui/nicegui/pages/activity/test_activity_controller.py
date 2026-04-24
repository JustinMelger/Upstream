from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.shared_activity.controller import ActivityPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_activity_controller_load_events_calls_notifications_service(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, str]] = []

    async def _fake_load_activity_feed(*, api, limit: int, scope: str):  # noqa: ANN001
        calls.append((limit, scope))
        return [{"message": "hello"}, "bad", {"message": "world"}]

    from frontend.ui.nicegui.pages.shared_activity import controller as activity_controller

    monkeypatch.setattr(activity_controller, "load_activity_feed", _fake_load_activity_feed)

    class _Api:
        async def get(self, *_args, **_kwargs):  # noqa: ANN001
            return []

    c = ActivityPageController(api=_Api())  # type: ignore[arg-type]
    out = await c.load_events(scope="team", limit=50)
    assert out == [{"message": "hello"}, {"message": "world"}]
    assert calls == [(50, "team")]
