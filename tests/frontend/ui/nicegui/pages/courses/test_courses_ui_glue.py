from __future__ import annotations

from frontend.ui.nicegui.pages.courses.ui_glue import (
    build_active_filter_chips,
    compute_courses_meta_text,
    compute_expanded_visible_count,
    default_courses_filter_reset_state,
    normalize_course_tracking_status,
    primary_course_cta_label_for_status,
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


def test_compute_courses_meta_text() -> None:
    assert compute_courses_meta_text(course_count=0) == "0 courses"
    assert compute_courses_meta_text(course_count=12) == "12 courses"


def test_compute_expanded_visible_count_caps_total() -> None:
    assert compute_expanded_visible_count(current_visible=10, total_count=25, page_size=10) == 20
    assert compute_expanded_visible_count(current_visible=20, total_count=25, page_size=10) == 25


def test_normalize_course_tracking_status_accepts_only_known_values() -> None:
    assert normalize_course_tracking_status("interested") == "interested"
    assert normalize_course_tracking_status("in_progress") == "in_progress"
    assert normalize_course_tracking_status("completed") == "completed"
    assert normalize_course_tracking_status("unknown") == ""
    assert normalize_course_tracking_status(None) == ""


def test_primary_course_cta_label_for_status_maps_expected_actions() -> None:
    assert primary_course_cta_label_for_status("in_progress") == "Continue"
    assert primary_course_cta_label_for_status("completed") == "Review"
    assert primary_course_cta_label_for_status("interested") == "Start"
    assert primary_course_cta_label_for_status("") == "Start"
