from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses import actions as courses_actions
from frontend.ui.nicegui.pages.courses.actions import build_course_card_actions


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_course_card_actions_wires_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _fake_copy_course_link(*, url: str) -> None:
        calls.append(f"copy:{url}")

    monkeypatch.setattr(courses_actions, "copy_course_link", _fake_copy_course_link)

    async def _open_details(course_id: int, focus_reviews: bool) -> None:
        calls.append(f"open:{course_id}:{focus_reviews}")

    async def _open_recommend(course_id: int) -> None:
        calls.append(f"recommend:{course_id}")

    def _open_edit(course_row: dict) -> None:
        calls.append(f"edit:{int(course_row.get('id') or 0)}")

    async def _confirm_delete(course_id: int) -> None:
        calls.append(f"delete:{course_id}")

    cb = build_course_card_actions(
        course_id=7,
        course_url="https://example.com/course/7",
        course_row={"id": 7, "title": "FastAPI"},
        on_open_details=_open_details,
        on_open_recommend=_open_recommend,
        on_open_edit=_open_edit,
        on_confirm_delete=_confirm_delete,
    )

    await cb.on_view()
    await cb.on_review()
    await cb.on_recommend()
    cb.on_copy_link()
    cb.on_edit()
    await cb.on_delete()

    assert "open:7:False" in calls
    assert "open:7:True" in calls
    assert "recommend:7" in calls
    assert "copy:https://example.com/course/7" in calls
    assert "edit:7" in calls
    assert "delete:7" in calls
