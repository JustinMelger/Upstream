"""UI sections for the Learning page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_actions import render_view_review_actions
from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.errors import FrontendError, safe_notify


_ALLOWED_TRACKING_STATUSES = {"interested", "in_progress", "completed"}


def render_tracking_status_select(
    *,
    course_id: int,
    current_status: str,
    options_map: dict[str, str],
    resolve_status_value: Any,
    on_set_status: Any,
    on_clear_status: Any,
) -> Any:
    """Render tracking status select and wire update handling."""
    status_select = ui.select(
        options=options_map,
        value=current_status,
        label=None,
    ).props("dense")
    status_select.props("use-input hide-selected fill-input")
    status_select.tooltip("Status")

    async def _on_status_change(e: Any, _cid: int = int(course_id), _select=status_select) -> None:
        _select.disable()
        previous_value = str(_select.value or "")
        try:
            value = resolve_status_value(
                raw_event=e,
                options_map=options_map,
                fallback_value=str(_select.value or ""),
            )
            if value and value not in _ALLOWED_TRACKING_STATUSES:
                safe_notify(f"Invalid status: {value}", type="negative")
                _select.value = previous_value
                _select.update()
                return
            _select.value = value
            _select.update()
            if not value:
                try:
                    await on_clear_status(_cid)
                except (ApiError, FrontendError, RuntimeError):
                    _select.value = previous_value
                    _select.update()
                    raise
                return
            try:
                await on_set_status(_cid, value)
            except (ApiError, FrontendError, RuntimeError):
                _select.value = previous_value
                _select.update()
                raise
        finally:
            _select.enable()

    status_select.on("update:model-value", _on_status_change)
    return status_select


def render_tracked_courses_section(
    *,
    tracked_courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    course_review_summary_by_id: dict[int, dict[str, Any]],
    tracked_visible: int,
    review_summary_label: Any,
    tracking_label_fn: Any,
    tracking_chip_class_fn: Any,
    on_view_course: Any,
    on_review_course: Any,
    resolve_status_value: Any,
    on_set_status: Any,
    on_clear_status: Any,
    on_browse_courses: Any,
) -> None:
    """Render tracked-courses card and rows."""
    with ui.card().classes("lp-card w-full"):
        ui.label("Tracked courses").classes("text-md font-semibold")
        if not tracked_courses:
            ui.label("Track a course to see it here.").classes("text-sm").style("color: var(--lp-muted)")
            ui.button("Browse courses", on_click=on_browse_courses).props("dense outline")

        for c in tracked_courses[:tracked_visible]:
            cid = int(c.get("id") or 0)
            tr = tracking_by_course_id.get(cid) or {}
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-0"):
                    ui.label(str(c.get("title") or "")).classes("text-sm font-semibold")
                    provider = str(c.get("provider") or "").strip()
                    category = str(c.get("category") or "").strip()
                    bits = [b for b in [provider, category] if b]
                    if bits:
                        ui.label(" · ".join(bits)).classes("text-xs").style("color: var(--lp-muted)")
                    review_badge = review_summary_label(course_review_summary_by_id.get(cid))
                    if review_badge:
                        ui.label(review_badge).classes("text-xs").style("color: var(--lp-muted)")

                with ui.row().classes("items-center gap-2"):
                    ui.label(tracking_label_fn(tr.get("status"))).classes(tracking_chip_class_fn(tr.get("status")))
                    render_view_review_actions(on_view=on_view_course(cid), on_review=on_review_course(cid))
                    options_map = {
                        "": "Not tracked",
                        **{k: v for k, v in TRACKING_STATUS_OPTIONS},
                    }
                    render_tracking_status_select(
                        course_id=cid,
                        current_status=str(tr.get("status") or ""),
                        options_map=options_map,
                        resolve_status_value=resolve_status_value,
                        on_set_status=on_set_status,
                        on_clear_status=on_clear_status,
                    )


def render_selected_paths_section(
    *,
    selected_paths: list[dict[str, Any]],
    selected_visible: int,
    path_details_by_id: dict[int, dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    path_review_summary_by_id: dict[int, dict[str, Any]],
    progress_for_path_detail: Any,
    review_summary_label: Any,
    on_view_path: Any,
    on_review_path: Any,
    on_browse_paths: Any,
) -> None:
    """Render selected-paths card and rows."""
    with ui.card().classes("lp-card w-full"):
        ui.label("Selected paths").classes("text-md font-semibold")
        if not selected_paths:
            ui.label("Select a path to track progress.").classes("text-sm").style("color: var(--lp-muted)")
            ui.button("Browse paths", on_click=on_browse_paths).props("dense outline")

        for row in selected_paths[:selected_visible]:
            pid = int(row.get("id") or 0)
            detail = path_details_by_id.get(pid) or {}
            completed, total, ratio = progress_for_path_detail(
                detail=detail,
                tracking_by_course_id=tracking_by_course_id,
            )
            with ui.column().classes("w-full gap-1"):
                ui.label(str(row.get("name") or "")).classes("text-sm font-semibold")
                ui.label("Tracked").classes("lp-chip lp-chip--sky")
                review_badge = review_summary_label(path_review_summary_by_id.get(pid))
                if review_badge:
                    ui.label(review_badge).classes("text-xs").style("color: var(--lp-muted)")
                if total:
                    ui.label(f"{completed}/{total} completed").classes("text-xs").style("color: var(--lp-muted)")
                    ui.linear_progress(ratio, show_value=False).classes("w-full")
                with ui.row().classes("items-center gap-2"):
                    render_view_review_actions(on_view=on_view_path(pid), on_review=on_review_path(pid))


def render_shared_content(
    *,
    shared_courses: list[dict[str, Any]],
    shared_paths: list[dict[str, Any]],
    shared_articles: list[dict[str, Any]],
    shared_course_review_summary_by_id: dict[int, dict[str, Any]],
    shared_course_recommendation_summary_by_id: dict[int, dict[str, Any]],
    shared_path_review_summary_by_id: dict[int, dict[str, Any]],
    shared_path_recommendation_summary_by_id: dict[int, dict[str, Any]],
    review_summary_label: Any,
    recommendation_summary_label: Any,
    on_view_course: Any,
    on_review_course: Any,
    on_view_path: Any,
    on_review_path: Any,
    feature_articles: bool,
    on_open_articles: Any,
) -> None:
    """Render shared tab content."""
    ui.label("Shared by you").classes("text-lg font-semibold mt-2")

    with ui.card().classes("lp-card w-full"):
        ui.label("Courses").classes("text-md font-semibold")
        if not shared_courses:
            ui.label("You haven't shared any courses yet.").classes("text-sm").style("color: var(--lp-muted)")
        for c in shared_courses[:12]:
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-0"):
                    ui.label(str(c.get("title") or "")).classes("text-sm")
                    cid = int(c.get("id") or 0)
                    parts = [
                        review_summary_label(shared_course_review_summary_by_id.get(cid)),
                        recommendation_summary_label(shared_course_recommendation_summary_by_id.get(cid)),
                    ]
                    parts = [part for part in parts if part]
                    if parts:
                        ui.label(" · ".join(parts)).classes("text-xs").style("color: var(--lp-muted)")
                cid = int(c.get("id") or 0)
                with ui.row().classes("items-center gap-2"):
                    render_view_review_actions(on_view=on_view_course(cid), on_review=on_review_course(cid))

    with ui.card().classes("lp-card w-full"):
        ui.label("Paths").classes("text-md font-semibold")
        if not shared_paths:
            ui.label("You haven't shared any paths yet.").classes("text-sm").style("color: var(--lp-muted)")
        for p in shared_paths[:12]:
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-0"):
                    ui.label(str(p.get("name") or "")).classes("text-sm")
                    pid = int(p.get("id") or 0)
                    parts = [
                        review_summary_label(shared_path_review_summary_by_id.get(pid)),
                        recommendation_summary_label(shared_path_recommendation_summary_by_id.get(pid)),
                    ]
                    parts = [part for part in parts if part]
                    if parts:
                        ui.label(" · ".join(parts)).classes("text-xs").style("color: var(--lp-muted)")
                pid = int(p.get("id") or 0)
                with ui.row().classes("items-center gap-2"):
                    render_view_review_actions(on_view=on_view_path(pid), on_review=on_review_path(pid))

    if feature_articles:
        with ui.card().classes("lp-card w-full"):
            ui.label("Articles").classes("text-md font-semibold")
            if not shared_articles:
                ui.label("You haven't shared any articles yet.").classes("text-sm").style("color: var(--lp-muted)")
            for a in shared_articles[:12]:
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(str(a.get("title") or "")).classes("text-sm")
                    ui.button("Open", on_click=on_open_articles).props("dense outline")


def render_recommended_section(
    *,
    recommended_courses: list[dict[str, Any]],
    recommended_paths: list[dict[str, Any]],
    on_save_recommended_course: Any,
    on_save_recommended_path: Any,
    on_dismiss_recommended_course: Any,
    on_dismiss_recommended_path: Any,
    on_view_course: Any,
    on_view_path: Any,
) -> None:
    """Render recommendation card in learning tab."""
    with ui.card().classes("lp-card w-full"):
        ui.label("Recommended for you").classes("text-md font-semibold")
        if not recommended_courses and not recommended_paths:
            ui.label("No recommendations yet.").classes("text-sm").style("color: var(--lp-muted)")
        for row in recommended_courses[:5]:
            course = dict(row.get("course") or {})
            cid = int(row.get("course_id") or 0)
            why = str(row.get("why") or "").strip()
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-0"):
                    ui.label(str(course.get("title") or "")).classes("text-sm font-semibold")
                    if why:
                        ui.label(why).classes("text-xs").style("color: var(--lp-muted)")
                with ui.row().classes("items-center gap-2"):
                    ui.button("Save", on_click=lambda _cid=cid: on_save_recommended_course(_cid)).props("dense outline")
                    ui.button(
                        "Dismiss",
                        on_click=lambda _cid=cid: on_dismiss_recommended_course(_cid),
                    ).props("dense flat")
                    ui.button("", icon="visibility", on_click=on_view_course(cid)).props("outline dense").tooltip("View")

        for row in recommended_paths[:5]:
            path = dict(row.get("path") or {})
            pid = int(row.get("path_id") or 0)
            why = str(row.get("why") or "").strip()
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-0"):
                    ui.label(str(path.get("name") or "")).classes("text-sm font-semibold")
                    if why:
                        ui.label(why).classes("text-xs").style("color: var(--lp-muted)")
                with ui.row().classes("items-center gap-2"):
                    ui.button("Save", on_click=lambda _pid=pid: on_save_recommended_path(_pid)).props("dense outline")
                    ui.button(
                        "Dismiss",
                        on_click=lambda _pid=pid: on_dismiss_recommended_path(_pid),
                    ).props("dense flat")
                    ui.button("", icon="visibility", on_click=on_view_path(pid)).props("outline dense").tooltip("View")


def render_continue_learning_section(*, next_course: dict[str, Any], on_open_selected_paths: Any) -> None:
    """Render continue-learning card for next step."""
    nxt = dict(next_course.get("course") or {})
    with ui.card().classes("lp-card w-full"):
        ui.label("Continue learning").classes("text-md font-semibold")
        ui.label(str(nxt.get("title") or "")).classes("text-sm font-semibold")
        path_name = str(next_course.get("path_name") or "").strip()
        if path_name:
            ui.label(f"From {path_name}").classes("text-xs").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            url = str(nxt.get("url") or "").strip()
            if url:
                ui.button("Continue", on_click=lambda u=url: ui.navigate.to(u, new_tab=True)).props("dense outline")
            ui.button("Open path", on_click=on_open_selected_paths).props("dense outline")


def render_review_nudges_section(
    *,
    pending_course_review_ids: list[int],
    pending_path_review_ids: list[int],
    on_open_first_course_review: Any,
    on_open_first_path_review: Any,
) -> None:
    """Render review nudge card."""
    with ui.card().classes("lp-card w-full"):
        ui.label("Review nudges").classes("text-md font-semibold")
        if not pending_course_review_ids and not pending_path_review_ids:
            ui.label("You're up to date on reviews.").classes("text-sm").style("color: var(--lp-muted)")
            return
        if pending_course_review_ids:
            ui.label(f"{len(pending_course_review_ids)} tracked course(s) need your review.").classes("text-sm")
            ui.button("Review courses", on_click=on_open_first_course_review).props("dense outline")
        if pending_path_review_ids:
            ui.label(f"{len(pending_path_review_ids)} selected path(s) need your review.").classes("text-sm")
            ui.button("Review paths", on_click=on_open_first_path_review).props("dense outline")


def render_shared_tab(
    *,
    shared_vm: Any,
    review_summary_label: Any,
    recommendation_summary_label: Any,
    nav_actions: Any,
    feature_articles: bool,
    on_open_articles: Any,
) -> None:
    """Compose shared-tab UI from the shared view-model."""
    render_shared_content(
        shared_courses=shared_vm.shared_courses,
        shared_paths=shared_vm.shared_paths,
        shared_articles=shared_vm.shared_articles,
        shared_course_review_summary_by_id=shared_vm.shared_course_review_summary_by_id,
        shared_course_recommendation_summary_by_id=shared_vm.shared_course_recommendation_summary_by_id,
        shared_path_review_summary_by_id=shared_vm.shared_path_review_summary_by_id,
        shared_path_recommendation_summary_by_id=shared_vm.shared_path_recommendation_summary_by_id,
        review_summary_label=review_summary_label,
        recommendation_summary_label=recommendation_summary_label,
        on_view_course=nav_actions.make_course_view_action,
        on_review_course=nav_actions.make_course_review_action,
        on_view_path=nav_actions.make_path_view_action,
        on_review_path=nav_actions.make_path_review_action,
        feature_articles=bool(feature_articles),
        on_open_articles=on_open_articles,
    )


def render_learning_tab(
    *,
    learning_vm: Any,
    state: Any,
    next_course: dict[str, Any] | None,
    first_course_review_action: Any,
    first_path_review_action: Any,
    review_summary_label: Any,
    tracking_label_fn: Any,
    tracking_chip_class_fn: Any,
    resolve_status_value: Any,
    progress_for_path_detail: Any,
    nav_actions: Any,
    on_save_recommended_course: Any,
    on_save_recommended_path: Any,
    on_dismiss_recommended_course: Any,
    on_dismiss_recommended_path: Any,
    on_set_tracking_status: Any,
    on_clear_tracking_status: Any,
    on_browse_courses: Any,
    on_browse_paths: Any,
    on_open_selected_paths: Any,
    on_load_more_tracked: Any,
    on_load_more_selected: Any,
) -> None:
    """Compose learning-tab UI from the learning view-model."""
    ui.label("Learning").classes("text-lg font-semibold mt-2")

    render_recommended_section(
        recommended_courses=learning_vm.recommended_courses,
        recommended_paths=learning_vm.recommended_paths,
        on_save_recommended_course=on_save_recommended_course,
        on_save_recommended_path=on_save_recommended_path,
        on_dismiss_recommended_course=on_dismiss_recommended_course,
        on_dismiss_recommended_path=on_dismiss_recommended_path,
        on_view_course=nav_actions.make_course_view_action,
        on_view_path=nav_actions.make_path_view_action,
    )

    if next_course is not None:
        render_continue_learning_section(
            next_course=next_course,
            on_open_selected_paths=on_open_selected_paths,
        )

    render_review_nudges_section(
        pending_course_review_ids=learning_vm.pending_course_review_ids,
        pending_path_review_ids=learning_vm.pending_path_review_ids,
        on_open_first_course_review=first_course_review_action,
        on_open_first_path_review=first_path_review_action,
    )

    render_tracked_courses_section(
        tracked_courses=learning_vm.tracked_courses,
        tracking_by_course_id=learning_vm.tracking_by_course_id,
        course_review_summary_by_id=learning_vm.course_review_summary_by_id,
        tracked_visible=state.tracked_visible,
        review_summary_label=review_summary_label,
        tracking_label_fn=tracking_label_fn,
        tracking_chip_class_fn=tracking_chip_class_fn,
        on_view_course=nav_actions.make_course_view_action,
        on_review_course=nav_actions.make_course_review_action,
        resolve_status_value=resolve_status_value,
        on_set_status=on_set_tracking_status,
        on_clear_status=on_clear_tracking_status,
        on_browse_courses=on_browse_courses,
    )
    if len(learning_vm.tracked_courses) > state.tracked_visible:
        ui.button(
            f"Load more ({state.tracked_visible}/{len(learning_vm.tracked_courses)})",
            on_click=on_load_more_tracked,
        ).props("outline dense")

    render_selected_paths_section(
        selected_paths=learning_vm.selected_paths,
        selected_visible=state.selected_visible,
        path_details_by_id=learning_vm.path_details_by_id,
        tracking_by_course_id=learning_vm.tracking_by_course_id,
        path_review_summary_by_id=learning_vm.path_review_summary_by_id,
        progress_for_path_detail=progress_for_path_detail,
        review_summary_label=review_summary_label,
        on_view_path=nav_actions.make_path_view_action,
        on_review_path=nav_actions.make_path_review_action,
        on_browse_paths=on_browse_paths,
    )
    if len(learning_vm.selected_paths) > state.selected_visible:
        ui.button(
            f"Load more ({state.selected_visible}/{len(learning_vm.selected_paths)})",
            on_click=on_load_more_selected,
        ).props("outline dense")
