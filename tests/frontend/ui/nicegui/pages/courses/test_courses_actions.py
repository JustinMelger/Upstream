from __future__ import annotations

import pytest

from frontend.ui.nicegui.domains.courses import actions as courses_actions
from frontend.ui.nicegui.domains.courses.actions import (
    build_course_card_actions,
    clear_course_filter_by_key,
    CoursesFilterControls,
    recompute_course_facet_controls,
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

    def _open_edit(course_row: dict) -> None:
        calls.append(f"edit:{int(course_row.get('id') or 0)}")

    async def _confirm_delete(course_id: int) -> None:
        calls.append(f"delete:{course_id}")

    cb = build_course_card_actions(
        course_id=7,
        course_url="https://example.com/course/7",
        course_row={"id": 7, "title": "FastAPI"},
        on_open_details=_open_details,
        on_open_edit=_open_edit,
        on_confirm_delete=_confirm_delete,
    )

    await cb.on_view()
    await cb.on_review()
    cb.on_copy_link()
    cb.on_edit()
    await cb.on_delete()

    assert "open:7:False" in calls
    assert "open:7:True" in calls
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


@pytest.mark.unit
def test_recompute_course_facet_controls_applies_options_preserves_selected_and_updates() -> None:
    controls = CoursesFilterControls(
        scope_filter=_Control("all"),
        search_input=_Control("api"),
        provider_filter=_Control("ChosenProvider"),
        category_filter=_Control("ChosenCategory"),
        level_filter=_Control("ChosenLevel"),
        status_filter=_Control("completed"),
        sort_filter=_Control("newest"),
    )
    normalized = type(
        "Normalized",
        (),
        dict(
            scope="all",
            search="api",
            provider="chosenprovider",
            category="chosencategory",
            level="chosenlevel",
            status="completed",
        ),
    )()

    def _fake_counts(**_kwargs):
        return ({"OtherProvider": 2}, {"OtherCategory": 1}, {"OtherLevel": 1}, {"completed": 3})

    def _fake_build_count_options(*, any_label: str, counts: dict[str, int]) -> dict[str, str]:
        out: dict[str, str] = {"": any_label}
        out.update({k: f"{k} ({v})" for k, v in counts.items()})
        return out

    def _fake_build_status_options(*, status_counts: dict[str, int]) -> dict[str, str]:
        return {"": "Any status", "completed": f"Completed ({status_counts.get('completed', 0)})"}

    recompute_course_facet_controls(
        controls=controls,
        courses=[],
        tracking_by_course_id={},
        normalized_filters=normalized,
        compute_facet_counts=_fake_counts,
        build_count_options=_fake_build_count_options,
        build_status_options=_fake_build_status_options,
    )
    assert "ChosenProvider" in controls.provider_filter.options
    assert "ChosenCategory" in controls.category_filter.options
    assert "ChosenLevel" in controls.level_filter.options
    assert controls.provider_filter.value == "ChosenProvider"
    assert controls.category_filter.value == "ChosenCategory"
    assert controls.level_filter.value == "ChosenLevel"
    assert controls.status_filter.value == "completed"
    assert controls.provider_filter.updated == 1
    assert controls.category_filter.updated == 1
    assert controls.level_filter.updated == 1
    assert controls.status_filter.updated == 1


@pytest.mark.unit
def test_recompute_course_facet_controls_preserves_selected_facet_values_but_clears_invalid_status() -> None:
    controls = CoursesFilterControls(
        scope_filter=_Control("all"),
        search_input=_Control("api"),
        provider_filter=_Control("ProviderX"),
        category_filter=_Control("CategoryX"),
        level_filter=_Control("LevelX"),
        status_filter=_Control("in_progress"),
        sort_filter=_Control(""),
    )
    normalized = type(
        "Normalized",
        (),
        dict(
            scope="all",
            search="api",
            provider="",
            category="",
            level="",
            status="",
        ),
    )()

    def _fake_counts(**_kwargs):
        return ({"ProviderA": 1}, {"CategoryA": 1}, {"LevelA": 1}, {"completed": 2})

    def _fake_build_count_options(*, any_label: str, counts: dict[str, int]) -> dict[str, str]:
        out: dict[str, str] = {"": any_label}
        out.update({k: f"{k} ({v})" for k, v in counts.items()})
        return out

    def _fake_build_status_options(*, status_counts: dict[str, int]) -> dict[str, str]:
        return {"": "Any status", "completed": f"Completed ({status_counts.get('completed', 0)})"}

    recompute_course_facet_controls(
        controls=controls,
        courses=[],
        tracking_by_course_id={},
        normalized_filters=normalized,
        compute_facet_counts=_fake_counts,
        build_count_options=_fake_build_count_options,
        build_status_options=_fake_build_status_options,
    )
    assert controls.provider_filter.value == "ProviderX"
    assert controls.category_filter.value == "CategoryX"
    assert controls.level_filter.value == "LevelX"
    assert controls.status_filter.value == ""
