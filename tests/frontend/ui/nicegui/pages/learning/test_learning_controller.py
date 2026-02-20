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
async def test_learning_controller_tracking_and_save_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int, str]] = []

    from frontend.ui.nicegui.pages.learning import controller as learning_controller

    async def _set_tracking_status(*, api, course_id: int, status: str):  # noqa: ANN001
        calls.append(("set", course_id, status))

    async def _clear_tracking_status(*, api, course_id: int):  # noqa: ANN001
        calls.append(("clear", course_id, ""))

    async def _save_recommended_course(*, api, course_id: int):  # noqa: ANN001
        calls.append(("save_course", course_id, "interested"))

    async def _save_recommended_path(*, api, path_id: int):  # noqa: ANN001
        calls.append(("save_path", path_id, "selected"))

    monkeypatch.setattr(learning_controller, "set_tracking_status", _set_tracking_status)
    monkeypatch.setattr(learning_controller, "clear_tracking_status", _clear_tracking_status)
    monkeypatch.setattr(learning_controller, "save_recommended_course", _save_recommended_course)
    monkeypatch.setattr(learning_controller, "save_recommended_path", _save_recommended_path)

    c = LearningPageController(api=object())  # type: ignore[arg-type]
    await c.set_tracking_status(course_id=3, status="in_progress")
    await c.clear_tracking_status(course_id=3)
    await c.save_recommended_course(course_id=9)
    await c.save_recommended_path(path_id=4)

    assert calls == [
        ("set", 3, "in_progress"),
        ("clear", 3, ""),
        ("save_course", 9, "interested"),
        ("save_path", 4, "selected"),
    ]
