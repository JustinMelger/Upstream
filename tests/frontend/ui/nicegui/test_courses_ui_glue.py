from __future__ import annotations

from frontend.ui.nicegui.pages.courses.ui_glue import (
    build_active_filter_chips,
    default_courses_filter_reset_state,
    resolve_tracking_status_value,
)


def test_build_active_filter_chips_includes_selected_filters() -> None:
    chips = build_active_filter_chips(
        scope_value="tracked",
        search_value="fastapi",
        provider_value="FastAPI Docs",
        category_value="Backend",
        level_value="Beginner",
        status_value="interested",
        status_options={"interested": "Interested"},
    )
    assert [c.key for c in chips] == ["scope", "search", "provider", "category", "level", "status"]
    assert chips[-1].label == "Status: Interested"


def test_build_active_filter_chips_omits_empty_values() -> None:
    chips = build_active_filter_chips(
        scope_value="all",
        search_value="",
        provider_value="",
        category_value="",
        level_value="",
        status_value="",
        status_options={},
    )
    assert chips == []


def test_resolve_tracking_status_value_accepts_direct_value() -> None:
    options = {"": "Not tracked", "completed": "Completed"}
    value = resolve_tracking_status_value(raw_event="completed", options_map=options, fallback_value="")
    assert value == "completed"


def test_resolve_tracking_status_value_accepts_dict_label() -> None:
    options = {"": "Not tracked", "in_progress": "In progress"}
    value = resolve_tracking_status_value(
        raw_event={"label": "In progress"},
        options_map=options,
        fallback_value="",
    )
    assert value == "in_progress"


def test_default_courses_filter_reset_state_resets_scope_and_all_fields() -> None:
    reset = default_courses_filter_reset_state()
    assert reset.scope == "all"
    assert reset.search == ""
    assert reset.provider == ""
    assert reset.category == ""
    assert reset.level == ""
    assert reset.status == ""
    assert reset.sort == ""
