from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.controller import CoursesPageController


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/courses":
            return [{"id": 7, "title": "FastAPI"}, {"id": 8, "title": "SQL"}]
        if path == "/tracking":
            return [{"course_id": 7, "status": "in_progress"}]
        if path == "/courses/reviews/summary":
            return [{"course_id": 7, "avg_rating": 4.5, "review_count": 2}]
        return {}


@pytest.mark.unit
@pytest.mark.anyio
async def test_courses_controller_load_list_bundle() -> None:
    api = _FakeApi()
    controller = CoursesPageController(api=api)

    bundle = await controller.load_list_bundle(params={"q": "fastapi"})

    assert [int(c["id"]) for c in bundle.courses] == [7, 8]
    assert bundle.tracking_by_course_id == {7: {"course_id": 7, "status": "in_progress"}}
    assert bundle.review_summary_by_course_id[7]["review_count"] == 2
    assert ("GET", "/courses", {"q": "fastapi"}) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_courses_controller_reload_tracking() -> None:
    api = _FakeApi()
    controller = CoursesPageController(api=api)

    tracking = await controller.reload_tracking()
    assert tracking == {7: {"course_id": 7, "status": "in_progress"}}

