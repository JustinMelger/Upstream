"""My learning page for the NiceGUI frontend.

This page provides an overview of:
- Learning: tracked courses + selected paths.
- Shared: content created by the current user (courses/paths/articles).
"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import status_chip_class, status_label, tracking_chip_class, tracking_label
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

                ui.label("Learning").classes("text-lg font-semibold mt-2")

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
                            ui.label(tracking_label(tr.get("status"))).classes(tracking_chip_class(tr.get("status")))

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
                            ui.label(status_label(str(row.get("status") or ""))).classes(
                                status_chip_class(str(row.get("status") or ""))
                            )
                            if total:
                                ui.label(f"{completed}/{total} completed").classes("text-xs").style("color: var(--lp-muted)")
                                ui.linear_progress(ratio, show_value=False).classes("w-full")
                            with ui.row().classes("items-center gap-2"):
                                ui.button("Open selected", on_click=lambda: ui.navigate.to("/paths?tab=selected")).props(
                                    "dense outline"
                                )

            await _load()
            content()
