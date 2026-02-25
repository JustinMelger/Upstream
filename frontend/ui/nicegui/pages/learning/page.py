"""Home page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation import build_courses_deep_link, build_paths_deep_link
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.summary_formatters import format_recommendation_summary, format_review_summary
from frontend.ui.nicegui.pages.learning.actions import (
    dismiss_recommended_course,
    dismiss_recommended_path,
    LearningNavigationActions,
    load_more_selected,
    load_more_tracked,
)
from frontend.ui.nicegui.pages.learning.controller import LearningPageController
from frontend.ui.nicegui.pages.learning.onboarding import (
    dismiss_home_intro,
    INTRO_STEPS,
    should_show_home_intro,
)
from frontend.ui.nicegui.pages.learning.route_init import resolve_learning_initial_view
from frontend.ui.nicegui.pages.learning.sections import (
    render_learning_tab,
    render_shared_tab,
)
from frontend.ui.nicegui.pages.learning.state import LearningPageState
from frontend.ui.nicegui.pages.learning.ui_glue import (
    compute_meta_text,
    compute_next_visibility,
    compute_path_progress,
    resolve_tracking_status_value,
)
from frontend.ui.nicegui.pages.learning.view_model import (
    build_learning_tab_view,
    build_recently_shared_in_teams,
    build_shared_tab_view,
)


def _progress_for_path_detail(
    *, detail: dict[str, Any], tracking_by_course_id: dict[int, dict[str, Any]]
) -> tuple[int, int, float]:
    """Compute (completed, total, ratio) for a path based on course tracking."""
    return compute_path_progress(detail=detail, tracking_by_course_id=tracking_by_course_id)


def _next_uncompleted_course_from_selected_paths(
    *,
    selected_paths: list[dict[str, Any]],
    path_details_by_id: dict[int, dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> dict[str, Any] | None:
    """Pick first uncompleted course from selected paths in path order."""
    for row in selected_paths:
        try:
            pid = int(row.get("id") or 0)
        except (TypeError, ValueError):
            continue
        detail = path_details_by_id.get(pid) or {}
        for course in list(detail.get("courses") or []):
            if not isinstance(course, dict):
                continue
            try:
                cid = int(course.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid <= 0:
                continue
            status = str((tracking_by_course_id.get(cid) or {}).get("status") or "")
            if status != "completed":
                return {"path_id": pid, "path_name": str(row.get("name") or ""), "course": course}
    return None


def _next_from_tracked_courses(
    *,
    tracked_courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> dict[str, Any] | None:
    """Pick next course from tracked courses when no selected-path next step exists."""
    in_progress: list[dict[str, Any]] = []
    interested: list[dict[str, Any]] = []
    for row in tracked_courses:
        try:
            cid = int(row.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if cid <= 0:
            continue
        status = str((tracking_by_course_id.get(cid) or {}).get("status") or "")
        if status == "in_progress":
            in_progress.append(row)
        elif status == "interested":
            interested.append(row)
    if in_progress:
        return in_progress[0]
    if interested:
        return interested[0]
    return None


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/home` route."""

    @ui.page("/home")
    async def learning_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Home", store=store, api=api)
        username = str(user.get("username") or "")
        controller = LearningPageController(api=api)
        nav_actions = LearningNavigationActions(
            username=username,
            build_course_navigation_url=lambda course_id, view: build_courses_deep_link(
                course_id=int(course_id),
                view=str(view),
            ),
            build_path_navigation_url=lambda path_id, view: build_paths_deep_link(
                path_id=int(path_id),
                view=str(view),
            ),
        )

        state = LearningPageState()
        request = getattr(ui.context.client, "request", None)
        initial_view = resolve_learning_initial_view(request=request)

        @guard_ui_action(title="Load failed")
        async def _load(*, reset_visibility: bool = True) -> None:
            if state.loading:
                return
            state.loading = True
            state.tracked_visible, state.selected_visible = compute_next_visibility(
                reset_visibility=bool(reset_visibility),
                page_size=int(state.page_size),
                tracked_visible=int(state.tracked_visible),
                selected_visible=int(state.selected_visible),
            )
            meta.text = "Loading..."
            content.refresh()
            try:
                state.data = await controller.load_page_data(
                    username=username,
                    include_articles=bool(settings.feature_articles),
                )
                meta.text = compute_meta_text(
                    data=state.data,
                    view=str(view_filter.value or ""),
                    feature_articles=bool(settings.feature_articles),
                )
            except ApiError as exc:
                safe_notify(str(exc), type="negative")
                state.data = {}
                meta.text = "Failed to load"
            finally:
                state.loading = False
                content.refresh()

        @guard_ui_action(title="Update tracking failed")
        async def _set_tracking_status(course_id: int, status: str) -> None:
            await controller.set_tracking_status(course_id=int(course_id), status=str(status))
            await _load(reset_visibility=False)

        @guard_ui_action(title="Update tracking failed")
        async def _clear_tracking_status(course_id: int) -> None:
            await controller.clear_tracking_status(course_id=int(course_id))
            await _load(reset_visibility=False)

        @guard_ui_action(title="Track course failed")
        async def _save_recommended_course(course_id: int) -> None:
            await controller.save_recommended_course(course_id=int(course_id))
            await _load(reset_visibility=False)

        @guard_ui_action(title="Select path failed")
        async def _save_recommended_path(path_id: int) -> None:
            await controller.save_recommended_path(path_id=int(path_id))
            await _load(reset_visibility=False)

        with render_container():
            ui.label(subtitle_for(PrimaryPage.HOME)).classes("text-sm text-gray-600")
            ui.label("").classes("h-1")

            @ui.refreshable
            def intro_panel() -> None:
                if not should_show_home_intro(storage_user=app.storage.user):
                    return
                with ui.card().classes("lp-card w-full"):
                    ui.label("Welcome to Home").classes("text-md font-semibold")
                    ui.label("Start here in three quick steps.").classes("text-sm").style("color: var(--lp-muted)")
                    for idx, step in enumerate(INTRO_STEPS, start=1):
                        with ui.row().classes("items-start gap-2 w-full"):
                            ui.label(str(idx)).classes("lp-chip lp-chip--sky")
                            with ui.column().classes("gap-0"):
                                ui.label(step.title).classes("text-sm font-semibold")
                                ui.label(step.body).classes("text-xs").style("color: var(--lp-muted)")

                    def _dismiss_intro() -> None:
                        dismiss_home_intro(storage_user=app.storage.user)
                        intro_panel.refresh()

                    with ui.row().classes("justify-end w-full"):
                        ui.button("Dismiss", on_click=_dismiss_intro).props("dense outline")

            intro_panel()

            with ui.row().classes("lp-topbar"):
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    view_filter = (
                        ui.radio({"learning": "Learning", "shared": "Shared"}, value=initial_view)
                        .props("inline dense")
                        .classes("text-sm")
                    )
                    meta = ui.label("").classes("lp-topbar-meta")
                    ui.button("Refresh", on_click=_load).props("dense outline")

            def _navigate_tab() -> None:
                nav_actions.navigate_tab(str(view_filter.value or "learning"))

            def _on_view_tab_change(*_: Any) -> None:
                _navigate_tab()
                content.refresh()

            view_filter.on("update:model-value", _on_view_tab_change)

            @ui.refreshable
            def content() -> None:
                if state.loading:
                    render_card_skeletons(count=4)
                    return

                if not state.data:
                    ui.label("No data loaded yet.").classes("text-sm").style("color: var(--lp-muted)")
                    ui.button("Refresh", on_click=_load).props("dense outline")
                    return

                if str(view_filter.value or "learning") == "shared":
                    shared_vm = build_shared_tab_view(data=state.data)

                    render_shared_tab(
                        shared_vm=shared_vm,
                        review_summary_label=lambda row: format_review_summary(row, style="star"),
                        recommendation_summary_label=format_recommendation_summary,
                        nav_actions=nav_actions,
                        feature_articles=bool(settings.feature_articles),
                        on_open_articles=lambda: ui.navigate.to("/explore?tab=articles"),
                    )

                    return

                # Learning view.
                learning_vm = build_learning_tab_view(
                    data=state.data,
                    dismissed_recommended_course_ids=state.dismissed_recommended_course_ids,
                    dismissed_recommended_path_ids=state.dismissed_recommended_path_ids,
                )
                recently_shared_in_teams = build_recently_shared_in_teams(
                    data=state.data,
                    username=username,
                    limit=6,
                )

                next_course = _next_uncompleted_course_from_selected_paths(
                    selected_paths=learning_vm.selected_paths,
                    path_details_by_id=learning_vm.path_details_by_id,
                    tracking_by_course_id=learning_vm.tracking_by_course_id,
                )
                if next_course is None:
                    fallback = _next_from_tracked_courses(
                        tracked_courses=learning_vm.tracked_courses,
                        tracking_by_course_id=learning_vm.tracking_by_course_id,
                    )
                    if fallback is not None:
                        next_course = {"path_id": 0, "path_name": "", "course": fallback}

                first_course_review_action: Any = lambda: None
                if learning_vm.pending_course_review_ids:
                    first_course_review_action = nav_actions.make_course_review_action(
                        int(learning_vm.pending_course_review_ids[0])
                    )
                first_path_review_action: Any = lambda: None
                if learning_vm.pending_path_review_ids:
                    first_path_review_action = nav_actions.make_path_review_action(int(learning_vm.pending_path_review_ids[0]))

                def _refresh_content() -> None:
                    content.refresh()

                render_learning_tab(
                    learning_vm=learning_vm,
                    state=state,
                    next_course=next_course,
                    first_course_review_action=first_course_review_action,
                    first_path_review_action=first_path_review_action,
                    review_summary_label=lambda row: format_review_summary(row, style="star"),
                    tracking_label_fn=tracking_label,
                    tracking_chip_class_fn=tracking_chip_class,
                    resolve_status_value=resolve_tracking_status_value,
                    progress_for_path_detail=_progress_for_path_detail,
                    nav_actions=nav_actions,
                    on_save_recommended_course=_save_recommended_course,
                    on_save_recommended_path=_save_recommended_path,
                    on_dismiss_recommended_course=lambda _cid: dismiss_recommended_course(
                        state=state,
                        course_id=int(_cid),
                        refresh=_refresh_content,
                    ),
                    on_dismiss_recommended_path=lambda _pid: dismiss_recommended_path(
                        state=state,
                        path_id=int(_pid),
                        refresh=_refresh_content,
                    ),
                    on_set_tracking_status=_set_tracking_status,
                    on_clear_tracking_status=_clear_tracking_status,
                    on_browse_courses=lambda: ui.navigate.to("/explore?tab=courses"),
                    on_browse_paths=lambda: ui.navigate.to("/explore?tab=paths"),
                    on_open_selected_paths=lambda: ui.navigate.to("/manage/paths?tab=selected"),
                    on_open_full_stats=lambda: ui.navigate.to("/profile/stats"),
                    recently_shared_in_teams=recently_shared_in_teams,
                    on_open_recently_shared_item=lambda row: (
                        ui.navigate.to(f"/explore/courses/{int(row.get('id') or 0)}")
                        if str(row.get("type") or "") == "course"
                        else (
                            ui.navigate.to(f"/explore/paths/{int(row.get('id') or 0)}")
                            if str(row.get("type") or "") == "path"
                            else ui.navigate.to("/explore?tab=articles")
                        )
                    ),
                    on_load_more_tracked=lambda: load_more_tracked(
                        state=state,
                        total_count=len(learning_vm.tracked_courses),
                        refresh=_refresh_content,
                    ),
                    on_load_more_selected=lambda: load_more_selected(
                        state=state,
                        total_count=len(learning_vm.selected_paths),
                        refresh=_refresh_content,
                    ),
                )

            await _load()
            content()
