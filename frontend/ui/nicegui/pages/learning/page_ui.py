"""UI helpers for the Home page route."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import tracking_label
from frontend.ui.nicegui.core.navigation import build_courses_deep_link, build_paths_deep_link
from frontend.ui.nicegui.core.path_items import path_course_ids
from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.pages.learning.actions import LearningNavigationActions, load_more_selected, load_more_tracked
from frontend.ui.nicegui.pages.learning.controller import LearningPageController
from frontend.ui.nicegui.pages.learning.onboarding import (
    dismiss_home_intro,
    INTRO_STEPS,
    should_show_home_intro,
)
from frontend.ui.nicegui.pages.learning.sections import (
    LearningTabContext,
    render_learning_tab,
    render_shared_tab,
)
from frontend.ui.nicegui.pages.learning.state import LearningPageState
from frontend.ui.nicegui.pages.learning.ui_glue import compute_path_progress
from frontend.ui.nicegui.pages.learning.view_model import (
    build_learning_tab_view,
    build_recently_shared_in_teams,
    build_shared_tab_view,
)


@dataclass(slots=True)
class LearningPageContext:
    """Bound page dependencies for the Home route."""

    username: str
    controller: LearningPageController
    nav_actions: LearningNavigationActions
    state: LearningPageState


def build_learning_page_context(*, username: str, controller: LearningPageController) -> LearningPageContext:
    """Construct the bound Home-page context."""
    return LearningPageContext(
        username=username,
        controller=controller,
        nav_actions=LearningNavigationActions(
            username=username,
            build_course_navigation_url=lambda course_id, view: build_courses_deep_link(
                course_id=int(course_id),
                view=str(view),
            ),
            build_path_navigation_url=lambda path_id, view: build_paths_deep_link(
                path_id=int(path_id),
                view=str(view),
            ),
        ),
        state=LearningPageState(),
    )


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
        for cid in path_course_ids(detail=detail):
            if cid <= 0:
                continue
            status = str((tracking_by_course_id.get(cid) or {}).get("status") or "")
            if status != "completed":
                return {"path_id": pid, "path_name": str(row.get("name") or ""), "course": {"id": cid}}
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


def make_recently_shared_item_opener() -> Any:
    """Build navigation callback for recently shared mixed-item rows."""

    def _open_recently_shared_item(row: dict[str, Any]) -> None:
        item_id = int(row.get("id") or 0)
        item_type = str(row.get("type") or "")
        if item_type == "course":
            ui.navigate.to(f"/explore/courses/{item_id}")
            return
        if item_type == "video":
            ui.navigate.to(f"/explore/videos/{item_id}")
            return
        if item_type == "path":
            ui.navigate.to(f"/explore/paths/{item_id}")
            return
        ui.navigate.to(f"/explore/articles/{item_id}")

    return _open_recently_shared_item


def render_intro_panel() -> None:
    """Render dismissible onboarding intro when applicable."""

    @ui.refreshable
    def intro_panel() -> None:
        if not should_show_home_intro(storage_user=app.storage.user):
            return
        with ui.card().classes("lp-card w-full"):
            ui.label("How to use Home").classes("text-md font-semibold")
            ui.label("Use this page to pick up the next useful learning action quickly.").classes("text-sm").style(
                "color: var(--lp-muted)"
            )
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


def render_empty_home_state(*, on_refresh: Any) -> None:
    """Render fallback UI when home data is unavailable."""
    with ui.element("div").classes("w-full lp-refresh-region"):
        ui.label("Home data is unavailable right now.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Refresh to reload your next actions and learning progress.").classes("text-sm").style(
            "color: var(--lp-muted)"
        )
        ui.button("Refresh home", on_click=on_refresh).props("dense outline")


def render_shared_view(*, state: LearningPageState, nav_actions: LearningNavigationActions) -> None:
    """Render the shared tab content."""
    shared_vm = build_shared_tab_view(data=state.data)
    with ui.element("div").classes("w-full lp-refresh-region"):
        render_shared_tab(
            shared_vm=shared_vm,
            review_summary_label=lambda row: format_review_summary(row, style="star"),
            nav_actions=nav_actions,
        )


def resolve_learning_tab_context(
    *,
    page_ctx: LearningPageContext,
    refresh_content: Any,
    on_set_tracking_status: Any,
    on_clear_tracking_status: Any,
) -> LearningTabContext:
    """Build the bundled learning-tab context from page state."""
    learning_vm = build_learning_tab_view(
        data=page_ctx.state.data,
    )
    recently_shared_in_teams = build_recently_shared_in_teams(
        data=page_ctx.state.data,
        username=page_ctx.username,
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
        first_course_review_action = page_ctx.nav_actions.make_course_review_action(
            int(learning_vm.pending_course_review_ids[0])
        )
    first_path_review_action: Any = lambda: None
    if learning_vm.pending_path_review_ids:
        first_path_review_action = page_ctx.nav_actions.make_path_review_action(int(learning_vm.pending_path_review_ids[0]))

    return LearningTabContext(
        learning_vm=learning_vm,
        state=page_ctx.state,
        next_course=next_course,
        first_course_review_action=first_course_review_action,
        first_path_review_action=first_path_review_action,
        review_summary_label=lambda row: format_review_summary(row, style="star"),
        tracking_label_fn=tracking_label,
        progress_for_path_detail=compute_path_progress,
        nav_actions=page_ctx.nav_actions,
        on_set_tracking_status=on_set_tracking_status,
        on_clear_tracking_status=on_clear_tracking_status,
        on_browse_courses=lambda: ui.navigate.to("/explore?tab=courses"),
        on_browse_paths=lambda: ui.navigate.to("/explore?tab=paths"),
        on_open_selected_paths=lambda: ui.navigate.to("/explore?tab=paths"),
        on_open_full_stats=lambda: ui.navigate.to("/profile/stats"),
        recently_shared_in_teams=recently_shared_in_teams,
        on_open_recently_shared_item=make_recently_shared_item_opener(),
        on_load_more_tracked=lambda: load_more_tracked(
            state=page_ctx.state,
            total_count=len(learning_vm.tracked_courses),
            refresh=refresh_content,
        ),
        on_load_more_selected=lambda: load_more_selected(
            state=page_ctx.state,
            total_count=len(learning_vm.selected_paths),
            refresh=refresh_content,
        ),
    )


def render_learning_view(
    *,
    page_ctx: LearningPageContext,
    refresh_content: Any,
    on_set_tracking_status: Any,
    on_clear_tracking_status: Any,
) -> None:
    """Render the learning tab content."""
    with ui.element("div").classes("w-full lp-refresh-region"):
        render_learning_tab(
            ctx=resolve_learning_tab_context(
                page_ctx=page_ctx,
                refresh_content=refresh_content,
                on_set_tracking_status=on_set_tracking_status,
                on_clear_tracking_status=on_clear_tracking_status,
            )
        )


def render_learning_content(
    *,
    page_ctx: LearningPageContext,
    on_refresh: Any,
    on_set_tracking_status: Any,
    on_clear_tracking_status: Any,
    current_view: str,
) -> None:
    """Render the Home page content area for the active tab."""
    if page_ctx.state.loading:
        render_card_skeletons(count=4)
        return
    if not page_ctx.state.data:
        render_empty_home_state(on_refresh=on_refresh)
        return
    if current_view == "shared":
        render_shared_view(state=page_ctx.state, nav_actions=page_ctx.nav_actions)
        return
    render_learning_view(
        page_ctx=page_ctx,
        refresh_content=on_refresh,
        on_set_tracking_status=on_set_tracking_status,
        on_clear_tracking_status=on_clear_tracking_status,
    )
