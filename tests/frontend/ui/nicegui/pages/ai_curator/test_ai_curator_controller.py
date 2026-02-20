from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.ai_curator.controller import AiCuratorPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_controller_generate_plan_normalizes_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    from frontend.ui.nicegui.pages.ai_curator import controller as ai_curator_controller

    calls: list[tuple[str, str, object]] = []

    async def _generate_plan(*, api, goal: str):  # noqa: ANN001
        calls.append(("generate", goal, api))
        return {"name": "Path A", "description": "desc"}, [{"title": "C1", "provider": "P1"}]

    monkeypatch.setattr(ai_curator_controller, "generate_plan", _generate_plan)

    marker_api = object()
    c = AiCuratorPageController(api=marker_api)  # type: ignore[arg-type]
    path, courses = await c.generate_plan(goal="Build API")

    assert path == {"name": "Path A", "description": "desc"}
    assert len(courses) == 1
    assert courses[0]["title"] == "C1"
    assert calls == [("generate", "Build API", marker_api)]


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_controller_apply_plan_creates_courses_path_and_selects(monkeypatch: pytest.MonkeyPatch) -> None:
    from frontend.ui.nicegui.pages.ai_curator import controller as ai_curator_controller

    calls: list[tuple[str, int, str, bool, object]] = []

    async def _apply_plan(*, api, draft_courses, path_name: str, path_description: str, select_for_me: bool):  # noqa: ANN001
        calls.append(("apply", len(list(draft_courses or [])), path_name, select_for_me, api))
        return 7

    monkeypatch.setattr(ai_curator_controller, "apply_plan", _apply_plan)

    marker_api = object()
    c = AiCuratorPageController(api=marker_api)  # type: ignore[arg-type]
    out = await c.apply_plan(
        draft_courses=[
            {"title": "A", "description": "", "provider": "P", "category": "X", "level": "L", "url": ""},
            {"title": "B", "description": "", "provider": "P", "category": "X", "level": "L", "url": ""},
        ],
        path_name="P1",
        path_description="D1",
        select_for_me=True,
    )

    assert out == 7
    assert calls == [("apply", 2, "P1", True, marker_api)]


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_controller_apply_plan_raises_on_invalid_created_course_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.ui.nicegui.pages.ai_curator import controller as ai_curator_controller

    async def _apply_plan(**_kwargs):  # noqa: ANN003
        raise RuntimeError("invalid_created_course_id")

    monkeypatch.setattr(ai_curator_controller, "apply_plan", _apply_plan)
    c = AiCuratorPageController(api=object())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="invalid_created_course_id"):
        await c.apply_plan(
            draft_courses=[{"title": "A"}],
            path_name="P1",
            path_description="D1",
            select_for_me=False,
        )


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_controller_apply_plan_raises_on_invalid_created_path_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.ui.nicegui.pages.ai_curator import controller as ai_curator_controller

    async def _apply_plan(**_kwargs):  # noqa: ANN003
        raise RuntimeError("invalid_created_path_id")

    monkeypatch.setattr(ai_curator_controller, "apply_plan", _apply_plan)
    c = AiCuratorPageController(api=object())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="invalid_created_path_id"):
        await c.apply_plan(
            draft_courses=[{"title": "A"}],
            path_name="P1",
            path_description="D1",
            select_for_me=False,
        )
