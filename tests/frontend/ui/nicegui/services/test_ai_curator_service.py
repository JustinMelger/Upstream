from __future__ import annotations

import pytest

from frontend.ui.nicegui.services import ai_curator_service


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_service_generate_plan_normalizes_rows() -> None:
    calls: list[tuple[str, dict]] = []

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            calls.append((path, payload))
            return {
                "path": {"name": "Path A", "description": "desc"},
                "courses": [{"title": "C1", "provider": "P1"}, "bad"],
            }

    path, courses = await ai_curator_service.generate_plan(api=_Api(), goal="Build API")  # type: ignore[arg-type]
    assert path == {"name": "Path A", "description": "desc"}
    assert len(courses) == 1
    assert courses[0]["title"] == "C1"
    assert calls == [("/ai/plan", {"goal": "Build API"})]


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_service_apply_plan_creates_courses_path_and_selects() -> None:
    calls: list[tuple[str, str, dict]] = []

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            calls.append(("POST", path, payload))
            if path == "/courses":
                return {"id": 11 if len([c for c in calls if c[1] == "/courses"]) == 1 else 12}
            if path == "/paths":
                return {"id": 7}
            return {}

    out = await ai_curator_service.apply_plan(
        api=_Api(),  # type: ignore[arg-type]
        draft_courses=[
            {"title": "A", "description": "", "provider": "P", "category": "X", "level": "L", "url": ""},
            {"title": "B", "description": "", "provider": "P", "category": "X", "level": "L", "url": ""},
        ],
        path_name="P1",
        path_description="D1",
        select_for_me=True,
    )
    assert out == 7
    assert calls[0][1] == "/courses"
    assert calls[1][1] == "/courses"
    assert calls[2] == (
        "POST",
        "/paths",
        {
            "name": "P1",
            "description": "D1",
            "items": [
                {"type": "course", "id": 11, "position": 0},
                {"type": "course", "id": 12, "position": 1},
            ],
        },
    )
    assert calls[3] == ("POST", "/paths/7/select", {})


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_service_apply_plan_raises_on_invalid_created_course_id() -> None:
    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            if path == "/courses":
                return {"id": 0}
            return {}

    with pytest.raises(RuntimeError, match="invalid_created_course_id"):
        await ai_curator_service.apply_plan(
            api=_Api(),  # type: ignore[arg-type]
            draft_courses=[{"title": "A"}],
            path_name="P1",
            path_description="D1",
            select_for_me=False,
        )


@pytest.mark.unit
@pytest.mark.anyio
async def test_ai_curator_service_apply_plan_raises_on_invalid_created_path_id() -> None:
    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            if path == "/courses":
                return {"id": 11}
            if path == "/paths":
                return {"id": 0}
            return {}

    with pytest.raises(RuntimeError, match="invalid_created_path_id"):
        await ai_curator_service.apply_plan(
            api=_Api(),  # type: ignore[arg-type]
            draft_courses=[{"title": "A"}],
            path_name="P1",
            path_description="D1",
            select_for_me=False,
        )
