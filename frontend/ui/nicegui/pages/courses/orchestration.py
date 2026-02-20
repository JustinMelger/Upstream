"""State orchestration helpers for the courses page."""

from __future__ import annotations

from typing import Any, Callable

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.courses.actions import CoursesFilterControls, reset_course_filter_controls
from frontend.ui.nicegui.pages.courses.filters import build_list_query_params
from frontend.ui.nicegui.pages.courses.state import CoursesPageState, CoursesPageUiState
from frontend.ui.nicegui.pages.courses.transitions import (
    begin_courses_load,
    clear_courses_state_on_load_error,
    finalize_courses_load,
)
from frontend.ui.nicegui.pages.courses.ui_glue import default_courses_filter_reset_state


def refresh_courses_list(
    *,
    ui_state: CoursesPageUiState,
    recompute_facet_options: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
) -> None:
    """Refresh list-level UI after filter updates."""
    ui_state.visible_count = int(ui_state.page_size)
    recompute_facet_options()
    refresh_active_filters()
    refresh_courses_list_ui()


def clear_course_filter_values(
    *,
    controls: CoursesFilterControls,
    refresh_active_filters: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
) -> None:
    """Reset all filter controls to their default values."""
    reset_course_filter_controls(
        controls=controls,
        reset_state=default_courses_filter_reset_state(),
    )
    refresh_active_filters()
    refresh_courses_list_ui()


async def load_courses(
    *,
    ui_state: CoursesPageUiState,
    page_state: CoursesPageState,
    controller: Any,
    controls: CoursesFilterControls,
    refresh_btn: Any,
    meta: Any,
    recompute_facet_options: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
    compute_meta_text: Callable[[int], str],
) -> None:
    """Load the courses list plus related summary maps."""
    if ui_state.loading:
        return
    ok = False
    load_start = begin_courses_load(page_size=ui_state.page_size)
    ui_state.loading = load_start.loading
    ui_state.visible_count = load_start.visible_count
    refresh_btn.disable()
    meta.text = load_start.meta_text
    refresh_courses_list_ui()
    try:
        params = build_list_query_params(
            search_value=str(controls.search_input.value or ""),
            provider_value=str(controls.provider_filter.value or ""),
            category_value=str(controls.category_filter.value or ""),
            level_value=str(controls.level_filter.value or ""),
        )

        bundle = await controller.load_list_bundle(params=params or None)
        page_state.courses = list(bundle.courses or [])
        page_state.tracking_by_course_id = dict(bundle.tracking_by_course_id or {})
        page_state.review_summary_by_course_id = dict(bundle.review_summary_by_course_id or {})
        page_state.recommendation_summary_by_course_id = dict(bundle.recommendation_summary_by_course_id or {})
        recompute_facet_options()
        refresh_courses_list_ui()
        ok = True
    except ApiError as exc:
        notify_error(str(exc))
        clear_courses_state_on_load_error(state=page_state)
        recompute_facet_options()
        refresh_courses_list_ui()
    finally:
        load_done = finalize_courses_load(ok=ok, course_count=len(page_state.courses))
        meta.text = compute_meta_text(len(page_state.courses))
        ui_state.loading = load_done.loading
        ui_state.loaded_once = load_done.loaded_once
        refresh_btn.enable()
        refresh_courses_list_ui()


async def reload_tracking_only(
    *,
    page_state: CoursesPageState,
    controller: Any,
    recompute_facet_options: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
) -> bool:
    """Reload tracking rows only."""
    try:
        page_state.tracking_by_course_id = await controller.reload_tracking()
    except ApiError as exc:
        notify_error(str(exc))
        page_state.tracking_by_course_id = {}
        refresh_courses_list_ui()
        return False
    recompute_facet_options()
    refresh_courses_list_ui()
    return True
