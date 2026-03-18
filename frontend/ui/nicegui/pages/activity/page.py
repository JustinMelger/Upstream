"""Activity feed page for shared/recommended notifications."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import FrontendError, guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation import build_activity_tab_link
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.activity.controller import ActivityPageController
from frontend.ui.nicegui.pages.activity.route_init import resolve_activity_tab
from frontend.ui.nicegui.pages.activity.sections import render_activity_error, render_activity_items, render_empty_activity
from frontend.ui.nicegui.pages.activity.state import ActivityPageState
from frontend.ui.nicegui.pages.activity.transitions import begin_activity_load, finalize_activity_load
from frontend.ui.nicegui.pages.activity.view_model import build_activity_event_views


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/teams` route."""

    @ui.page("/teams")
    async def activity_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        controller = ActivityPageController(api=api)
        state = ActivityPageState()

        render_shell(title="Teams", store=store, api=api)

        with render_container():
            request = getattr(ui.context.client, "request", None)
            initial_tab = resolve_activity_tab(request=request)
            ui.label(subtitle_for(PrimaryPage.TEAMS)).classes("text-sm text-gray-600 lp-teams-subtitle")

            with ui.row().classes("items-center justify-between w-full lp-teams-topbar"):
                tab_filter = (
                    ui.radio({"inbox": "Inbox", "team": "Team activity"}, value=initial_tab)
                    .props("inline dense")
                    .classes("text-sm lp-teams-tabs")
                )
                refresh_btn = ui.button("Refresh").props("dense outline").classes("lp-teams-refresh")

            @ui.refreshable
            def activity_list() -> None:
                current_tab = str(tab_filter.value or "inbox")
                if state.error_message:
                    render_activity_error(message=state.error_message, on_retry=_load)
                    return
                event_views = build_activity_event_views(events=state.events)
                if not event_views:
                    render_empty_activity(current_tab=current_tab, on_primary=lambda: ui.navigate.to("/explore"))
                    return
                render_activity_items(
                    events=event_views,
                    on_open=lambda target: ui.navigate.to(str(target.open_url)),
                )

            @guard_ui_action(title="Load activity failed")
            async def _load() -> None:
                if state.loading:
                    state.pending_reload = True
                    return
                state.pending_reload = True
                while state.pending_reload:
                    state.pending_reload = False
                    current_tab = str(tab_filter.value or "inbox")
                    scope = "team" if current_tab == "team" else "inbox"
                    load_start = begin_activity_load()
                    state.loading = load_start.loading
                    pending_error: Exception | None = None
                    try:
                        rows = await controller.load_events(scope=scope, limit=50)
                        load_done = finalize_activity_load(rows=rows)
                        state.events = list(load_done.events)
                        state.error_message = None
                    except (ApiError, RuntimeError) as exc:
                        state.events = []
                        state.error_message = str(exc)
                        pending_error = exc
                    finally:
                        state.loading = False
                        activity_list.refresh()
                    if pending_error is not None and not state.pending_reload:
                        raise FrontendError(status_code=500, message=str(pending_error))

            @guard_ui_action(title="Switch tab failed")
            async def _on_tab_change(*_args: Any) -> None:
                current = str(tab_filter.value or "inbox")
                ui.navigate.to(build_activity_tab_link(tab=current))
                await _load()

            tab_filter.on("update:model-value", _on_tab_change)
            refresh_btn.on_click(_load)
            activity_list()
            await _load()
