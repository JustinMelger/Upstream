"""My learning page for the NiceGUI frontend.

This page provides an overview of:
- Learning: tracked courses + selected paths.
- Shared: content created by the current user (courses/paths/articles).
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_actions import render_view_review_actions
from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.datetime_utils import format_date
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.learning_service import load_my_learning_data
from frontend.ui.nicegui.services.paths_service import compute_path_progress


_format_date = format_date


def _progress_for_path_detail(
    *, detail: dict[str, Any], tracking_by_course_id: dict[int, dict[str, Any]]
) -> tuple[int, int, float]:
    """Compute (completed, total, ratio) for a path based on course tracking."""
    return compute_path_progress(detail=detail, tracking_by_course_id=tracking_by_course_id)


def _review_summary_label(row: dict[str, Any] | None) -> str:
    """Format review summary as '★ 4.2 (12)'."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    return f"★ {avg:.1f} ({count})"


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


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/learning` route."""

    @ui.page("/learning")
    async def learning_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="My learning", store=store, api=api)
        username = str(user.get("username") or "")

        data: dict[str, Any] = {}
        loading = False

        request = getattr(ui.context.client, "request", None)
        query_params = getattr(request, "query_params", {}) if request is not None else {}
        initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "learning") or "").strip().lower()
        initial_view = "shared" if initial_tab == "shared" else "learning"

        @guard_ui_action(title="Load failed")
        async def _load() -> None:
            nonlocal data, loading
            if loading:
                return
            loading = True
            meta.text = "Loading..."
            content.refresh()
            try:
                data = await load_my_learning_data(
                    api=api,
                    username=username,
                    include_articles=bool(settings.feature_articles),
                )
                if str(view_filter.value or "") == "shared":
                    meta.text = (
                        f"{len(list(data.get('shared_courses') or []))} courses · "
                        f"{len(list(data.get('shared_paths') or []))} paths"
                        + (f" · {len(list(data.get('shared_articles') or []))} articles" if settings.feature_articles else "")
                    )
                else:
                    meta.text = (
                        f"{len(list(data.get('tracked_courses') or []))} tracked courses · "
                        f"{len(list(data.get('selected_paths') or []))} selected paths"
                    )
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                data = {}
                meta.text = "Failed to load"
            finally:
                loading = False
                content.refresh()

        with render_container():
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
                tab = str(view_filter.value or "learning")
                ui.navigate.to(f"/learning?tab={tab}")

            view_filter.on("update:model-value", lambda *_: _navigate_tab() or content.refresh())

            @ui.refreshable
            def content() -> None:
                if loading:
                    render_card_skeletons(count=4)
                    return

                if not data:
                    ui.label("No data loaded yet.").classes("text-sm").style("color: var(--lp-muted)")
                    return

                if str(view_filter.value or "learning") == "shared":
                    shared_courses = list(data.get("shared_courses") or [])
                    shared_paths = list(data.get("shared_paths") or [])
                    shared_articles = list(data.get("shared_articles") or [])

                    ui.label("Shared by you").classes("text-lg font-semibold mt-2")

                    with ui.card().classes("lp-card w-full"):
                        ui.label("Courses").classes("text-md font-semibold")
                        if not shared_courses:
                            ui.label("You haven't shared any courses yet.").classes("text-sm").style("color: var(--lp-muted)")
                        for c in shared_courses[:12]:
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(str(c.get("title") or "")).classes("text-sm")
                                ui.button(
                                    "Open",
                                    on_click=lambda: ui.navigate.to("/courses"),
                                ).props("dense outline")

                    with ui.card().classes("lp-card w-full"):
                        ui.label("Paths").classes("text-md font-semibold")
                        if not shared_paths:
                            ui.label("You haven't shared any paths yet.").classes("text-sm").style("color: var(--lp-muted)")
                        for p in shared_paths[:12]:
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(str(p.get("name") or "")).classes("text-sm")
                                ui.button(
                                    "Open",
                                    on_click=lambda: ui.navigate.to("/paths"),
                                ).props("dense outline")

                    if settings.feature_articles:
                        with ui.card().classes("lp-card w-full"):
                            ui.label("Articles").classes("text-md font-semibold")
                            if not shared_articles:
                                ui.label("You haven't shared any articles yet.").classes("text-sm").style(
                                    "color: var(--lp-muted)"
                                )
                            for a in shared_articles[:12]:
                                with ui.row().classes("items-center justify-between w-full"):
                                    ui.label(str(a.get("title") or "")).classes("text-sm")
                                    ui.button(
                                        "Open",
                                        on_click=lambda: ui.navigate.to("/articles"),
                                    ).props("dense outline")

                    return

                # Learning view.
                tracked_courses = list(data.get("tracked_courses") or [])
                tracking_by_course_id: dict[int, dict[str, Any]] = dict(data.get("tracking_by_course_id") or {})
                selected_paths = list(data.get("selected_paths") or [])
                path_details_by_id: dict[int, dict[str, Any]] = dict(data.get("path_details_by_id") or {})
                course_review_summary_by_id: dict[int, dict[str, Any]] = dict(data.get("course_review_summary_by_id") or {})
                path_review_summary_by_id: dict[int, dict[str, Any]] = dict(data.get("path_review_summary_by_id") or {})
                pending_course_review_ids = {int(i) for i in list(data.get("pending_course_review_ids") or [])}
                pending_path_review_ids = {int(i) for i in list(data.get("pending_path_review_ids") or [])}

                ui.label("Learning").classes("text-lg font-semibold mt-2")

                next_course = _next_uncompleted_course_from_selected_paths(
                    selected_paths=selected_paths,
                    path_details_by_id=path_details_by_id,
                    tracking_by_course_id=tracking_by_course_id,
                )
                if next_course is not None:
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
                                ui.button("Continue", on_click=lambda u=url: ui.navigate.to(u, new_tab=True)).props(
                                    "dense outline"
                                )
                            ui.button("Open path", on_click=lambda: ui.navigate.to("/paths?tab=selected")).props(
                                "dense outline"
                            )

                with ui.card().classes("lp-card w-full"):
                    ui.label("Review nudges").classes("text-md font-semibold")
                    if not pending_course_review_ids and not pending_path_review_ids:
                        ui.label("You're up to date on reviews.").classes("text-sm").style("color: var(--lp-muted)")
                    else:
                        if pending_course_review_ids:
                            ui.label(f"{len(pending_course_review_ids)} tracked course(s) need your review.").classes(
                                "text-sm"
                            )
                            ui.button("Review courses", on_click=lambda: ui.navigate.to("/courses?tab=tracked")).props(
                                "dense outline"
                            )
                        if pending_path_review_ids:
                            ui.label(f"{len(pending_path_review_ids)} selected path(s) need your review.").classes("text-sm")
                            ui.button("Review paths", on_click=lambda: ui.navigate.to("/paths?tab=selected")).props(
                                "dense outline"
                            )

                with ui.card().classes("lp-card w-full"):
                    ui.label("Tracked courses").classes("text-md font-semibold")
                    if not tracked_courses:
                        ui.label("Track a course to see it here.").classes("text-sm").style("color: var(--lp-muted)")
                        ui.button("Browse courses", on_click=lambda: ui.navigate.to("/courses")).props("dense outline")
                    for c in tracked_courses[:12]:
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
                                review_badge = _review_summary_label(course_review_summary_by_id.get(cid))
                                if review_badge:
                                    ui.label(review_badge).classes("text-xs").style("color: var(--lp-muted)")
                            with ui.row().classes("items-center gap-2"):
                                ui.label(tracking_label(tr.get("status"))).classes(tracking_chip_class(tr.get("status")))

                                async def _view_course(_cid: int = cid) -> None:
                                    ui.navigate.to("/courses?tab=tracked")

                                async def _review_course(_cid: int = cid) -> None:
                                    ui.navigate.to("/courses?tab=tracked")

                                render_view_review_actions(on_view=_view_course, on_review=_review_course)

                with ui.card().classes("lp-card w-full"):
                    ui.label("Selected paths").classes("text-md font-semibold")
                    if not selected_paths:
                        ui.label("Select a path to track progress.").classes("text-sm").style("color: var(--lp-muted)")
                        ui.button("Browse paths", on_click=lambda: ui.navigate.to("/paths")).props("dense outline")
                    for row in selected_paths[:12]:
                        pid = int(row.get("id") or 0)
                        detail = path_details_by_id.get(pid) or {}
                        completed, total, ratio = _progress_for_path_detail(
                            detail=detail, tracking_by_course_id=tracking_by_course_id
                        )
                        with ui.column().classes("w-full gap-1"):
                            ui.label(str(row.get("name") or "")).classes("text-sm font-semibold")
                            ui.label("Tracked").classes("lp-chip lp-chip--sky")
                            review_badge = _review_summary_label(path_review_summary_by_id.get(pid))
                            if review_badge:
                                ui.label(review_badge).classes("text-xs").style("color: var(--lp-muted)")
                            if total:
                                ui.label(f"{completed}/{total} completed").classes("text-xs").style("color: var(--lp-muted)")
                                ui.linear_progress(ratio, show_value=False).classes("w-full")
                            with ui.row().classes("items-center gap-2"):
                                async def _view_path(_pid: int = pid) -> None:
                                    ui.navigate.to("/paths?tab=selected")

                                async def _review_path(_pid: int = pid) -> None:
                                    ui.navigate.to("/paths?tab=selected")

                                render_view_review_actions(on_view=_view_path, on_review=_review_path)

            await _load()
            content()
