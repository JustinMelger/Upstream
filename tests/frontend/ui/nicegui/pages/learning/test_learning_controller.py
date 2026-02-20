from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.learning.controller import LearningPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_learning_controller_load_page_data_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, bool]] = []

    async def _fake_load_my_learning_data(*, api, username: str, include_articles: bool):  # noqa: ANN001
        calls.append((username, include_articles))
        return {"tracked_courses": []}

    from frontend.ui.nicegui.pages.learning import controller as learning_controller

    monkeypatch.setattr(learning_controller, "load_my_learning_data", _fake_load_my_learning_data)

    class _Api:
        async def post(self, *_args, **_kwargs):  # noqa: ANN001
            return {}

    c = LearningPageController(api=_Api())  # type: ignore[arg-type]
    out = await c.load_page_data(username="alice", include_articles=True)
    assert out == {"tracked_courses": []}
    assert calls == [("alice", True)]


@pytest.mark.unit
@pytest.mark.anyio
async def test_learning_controller_tracking_and_save_calls() -> None:
    calls: list[tuple[str, dict]] = []

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            calls.append((path, payload))
            return {}

    c = LearningPageController(api=_Api())  # type: ignore[arg-type]
    await c.set_tracking_status(course_id=3, status="in_progress")
    await c.clear_tracking_status(course_id=3)
    await c.save_recommended_course(course_id=9)
    await c.save_recommended_path(path_id=4)

    assert calls == [
        ("/tracking", {"course_id": 3, "status": "in_progress"}),
        ("/tracking/delete", {"course_id": 3}),
        ("/tracking", {"course_id": 9, "status": "interested"}),
        ("/paths/4/select", {}),
    ]
