from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses import actions as courses_actions
from frontend.ui.nicegui.pages.courses.actions import (
    CoursesFilterControls,
    build_course_card_actions,
    clear_course_filter_by_key,
    reset_course_filter_controls,
)


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


class _Control:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.updated = 0

    def update(self) -> None:
        self.updated += 1


@pytest.mark.unit
def test_clear_course_filter_by_key_updates_expected_control() -> None:
    controls = CoursesFilterControls(
        scope_filter=_Control("tracked"),
        search_input=_Control("needle"),
        provider_filter=_Control("provider"),
        category_filter=_Control("category"),
        level_filter=_Control("level"),
        status_filter=_Control("completed"),
        sort_filter=_Control("newest"),
    )
    assert clear_course_filter_by_key(key="search", controls=controls) is True
    assert controls.search_input.value == ""
    assert controls.search_input.updated == 1
    assert clear_course_filter_by_key(key="scope", controls=controls) is True
    assert controls.scope_filter.value == "all"
    assert controls.scope_filter.updated == 1
    assert clear_course_filter_by_key(key="unknown", controls=controls) is False


@pytest.mark.unit
def test_reset_course_filter_controls_sets_all_values_and_updates() -> None:
    controls = CoursesFilterControls(
        scope_filter=_Control("tracked"),
        search_input=_Control("needle"),
        provider_filter=_Control("provider"),
        category_filter=_Control("category"),
        level_filter=_Control("level"),
        status_filter=_Control("completed"),
        sort_filter=_Control("newest"),
    )
    reset = type("Reset", (), dict(scope="all", search="", provider="", category="", level="", status="", sort=""))()
    reset_course_filter_controls(controls=controls, reset_state=reset)
    assert controls.scope_filter.value == "all"
    assert controls.search_input.value == ""
    assert controls.provider_filter.value == ""
    assert controls.category_filter.value == ""
    assert controls.level_filter.value == ""
    assert controls.status_filter.value == ""
    assert controls.sort_filter.value == ""
    assert controls.scope_filter.updated == 1
    assert controls.search_input.updated == 1
    assert controls.provider_filter.updated == 1
    assert controls.category_filter.updated == 1
    assert controls.level_filter.updated == 1
    assert controls.status_filter.updated == 1
    assert controls.sort_filter.updated == 1
