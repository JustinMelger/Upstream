"""State orchestration helpers for the courses page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class CoursesListRefreshDeps:
    """Dependencies required to refresh list-level Courses UI blocks."""

    refresh_courses_list_ui: Callable[[], None]
    refresh_active_filters: Callable[[], None] | None = None
    recompute_facet_options: Callable[[], None] | None = None


@dataclass(frozen=True, slots=True)
class LoadCoursesDeps:
    """Dependencies required to load and refresh the Courses page."""

    controller: Any
    controls: CoursesFilterControls
    refresh_btn: Any
    meta: Any
    list_refresh: CoursesListRefreshDeps
    notify_error: Callable[[str], None]
    compute_meta_text: Callable[[int], str]


@dataclass(frozen=True, slots=True)
class CoursesTrackingRefreshDeps:
    """Dependencies required to refresh tracking-only Courses state."""

    list_refresh: CoursesListRefreshDeps
    notify_error: Callable[[str], None]


def refresh_courses_list(
    *,
    ui_state: CoursesPageUiState,
    deps: CoursesListRefreshDeps,
) -> None:
    """Refresh list-level UI after filter updates."""
    ui_state.visible_count = int(ui_state.page_size)
    if deps.recompute_facet_options is not None:
        deps.recompute_facet_options()
    if deps.refresh_active_filters is not None:
        deps.refresh_active_filters()
    deps.refresh_courses_list_ui()


def clear_course_filter_values(
    *,
    controls: CoursesFilterControls,
    deps: CoursesListRefreshDeps,
) -> None:
    """Reset all filter controls to their default values."""
    reset_course_filter_controls(
        controls=controls,
        reset_state=default_courses_filter_reset_state(),
    )
    if deps.refresh_active_filters is not None:
        deps.refresh_active_filters()
    deps.refresh_courses_list_ui()


async def load_courses(
    *,
    ui_state: CoursesPageUiState,
    page_state: CoursesPageState,
    deps: LoadCoursesDeps,
) -> None:
    """Load the courses list plus related summary maps."""
    if ui_state.loading:
        return
    ok = False
    load_start = begin_courses_load(page_size=ui_state.page_size)
    ui_state.loading = load_start.loading
    ui_state.visible_count = load_start.visible_count
    deps.refresh_btn.disable()
    deps.meta.text = load_start.meta_text
    deps.list_refresh.refresh_courses_list_ui()
    try:
        params = build_list_query_params(
            search_value=str(deps.controls.search_input.value or ""),
            provider_value=str(deps.controls.provider_filter.value or ""),
            category_value=str(deps.controls.category_filter.value or ""),
            level_value=str(deps.controls.level_filter.value or ""),
        )

        bundle = await deps.controller.load_list_bundle(params=params or None)
        page_state.courses = list(bundle.courses or [])
        page_state.tracking_by_course_id = dict(bundle.tracking_by_course_id or {})
        page_state.review_summary_by_course_id = dict(bundle.review_summary_by_course_id or {})
        if deps.list_refresh.recompute_facet_options is not None:
            deps.list_refresh.recompute_facet_options()
        deps.list_refresh.refresh_courses_list_ui()
        ok = True
    except ApiError as exc:
        deps.notify_error(str(exc))
        clear_courses_state_on_load_error(state=page_state)
        if deps.list_refresh.recompute_facet_options is not None:
            deps.list_refresh.recompute_facet_options()
        deps.list_refresh.refresh_courses_list_ui()
    finally:
        load_done = finalize_courses_load(ok=ok, course_count=len(page_state.courses))
        deps.meta.text = deps.compute_meta_text(len(page_state.courses))
        ui_state.loading = load_done.loading
        ui_state.loaded_once = load_done.loaded_once
        deps.refresh_btn.enable()
        deps.list_refresh.refresh_courses_list_ui()


async def reload_tracking_only(
    *,
    page_state: CoursesPageState,
    controller: Any,
    deps: CoursesTrackingRefreshDeps,
) -> bool:
    """Reload tracking rows only."""
    try:
        page_state.tracking_by_course_id = await controller.reload_tracking()
    except ApiError as exc:
        deps.notify_error(str(exc))
        page_state.tracking_by_course_id = {}
        deps.list_refresh.refresh_courses_list_ui()
        return False
    if deps.list_refresh.recompute_facet_options is not None:
        deps.list_refresh.recompute_facet_options()
    deps.list_refresh.refresh_courses_list_ui()
    return True


async def perform_set_tracking(
    *,
    course_id: int,
    status: str,
    controller: Any,
    page_state: CoursesPageState,
    deps: CoursesTrackingRefreshDeps,
) -> bool:
    """Persist tracking status and refresh tracking-only page state."""
    await controller.set_tracking_status(course_id=int(course_id), status=str(status))
    return await reload_tracking_only(
        page_state=page_state,
        controller=controller,
        deps=deps,
    )


async def perform_clear_tracking(
    *,
    course_id: int,
    controller: Any,
    page_state: CoursesPageState,
    deps: CoursesTrackingRefreshDeps,
) -> bool:
    """Clear tracking status and refresh tracking-only page state."""
    await controller.clear_tracking_status(course_id=int(course_id))
    return await reload_tracking_only(
        page_state=page_state,
        controller=controller,
        deps=deps,
    )


async def perform_create_course(
    *,
    payload: dict[str, Any],
    controller: Any,
    reload_page: Callable[[], Awaitable[None]],
) -> dict[str, Any]:
    """Create a course, then reload page data."""
    created = dict(await controller.create_course(payload=dict(payload or {})) or {})
    await reload_page()
    return created


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
