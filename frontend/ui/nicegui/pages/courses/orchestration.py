"""State orchestration helpers for the courses page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

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


async def perform_set_tracking(
    *,
    course_id: int,
    status: str,
    controller: Any,
    page_state: CoursesPageState,
    recompute_facet_options: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
) -> bool:
    """Persist tracking status and refresh tracking-only page state."""
    await controller.set_tracking_status(course_id=int(course_id), status=str(status))
    return await reload_tracking_only(
        page_state=page_state,
        controller=controller,
        recompute_facet_options=recompute_facet_options,
        refresh_courses_list_ui=refresh_courses_list_ui,
        notify_error=notify_error,
    )


async def perform_clear_tracking(
    *,
    course_id: int,
    controller: Any,
    page_state: CoursesPageState,
    recompute_facet_options: Callable[[], None],
    refresh_courses_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
) -> bool:
    """Clear tracking status and refresh tracking-only page state."""
    await controller.clear_tracking_status(course_id=int(course_id))
    return await reload_tracking_only(
        page_state=page_state,
        controller=controller,
        recompute_facet_options=recompute_facet_options,
        refresh_courses_list_ui=refresh_courses_list_ui,
        notify_error=notify_error,
    )


async def refresh_course_recommendation_summary(
    *,
    course_id: int,
    username: str,
    controller: Any,
    page_state: CoursesPageState,
    refresh_courses_list_ui: Callable[[], None],
) -> None:
    """Refresh recommendation summary map entry for a single course."""
    row = await controller.load_recommendation_summary_for_course(course_id=int(course_id))
    if isinstance(row, dict):
        page_state.recommendation_summary_by_course_id[int(course_id)] = row
    else:
        page_state.recommendation_summary_by_course_id.pop(int(course_id), None)
    controller.clear_course_detail_cache(course_id=int(course_id), cache_scope=str(username or ""))
    refresh_courses_list_ui()


async def perform_create_course(
    *,
    payload: dict[str, Any],
    controller: Any,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Create a course, then reload page data."""
    await controller.create_course(payload=dict(payload or {}))
    await reload_page()


async def perform_update_course(
    *,
    course_id: int,
    payload: dict[str, Any],
    controller: Any,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Update a course, then reload page data."""
    await controller.update_course(course_id=int(course_id), payload=dict(payload or {}))
    await reload_page()


async def perform_delete_course(
    *,
    course_id: int,
    controller: Any,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Delete a course, then reload page data."""
    await controller.delete_course(course_id=int(course_id))
    await reload_page()


async def perform_delete_course_from_dialog(
    course_id: int,
    *,
    controller: Any,
    reload_page: Callable[[], Awaitable[None]],
) -> None:
    """Adapter for dialog callbacks that pass positional course_id."""
    await perform_delete_course(
        course_id=int(course_id),
        controller=controller,
        reload_page=reload_page,
    )


async def open_delete_course_confirmation(
    course_id: int,
    *,
    open_delete_dialog: Callable[..., Awaitable[None]],
    on_delete_course: Callable[[int], Awaitable[None]],
) -> None:
    """Open delete-confirm dialog for a course with injected callbacks."""
    await open_delete_dialog(
        course_id=int(course_id),
        on_delete=on_delete_course,
    )
