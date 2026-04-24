"""Teams page route binder."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.shared_activity.route_init import resolve_activity_tab
from frontend.ui.nicegui.pages.teams.controller import TeamsPageController
from frontend.ui.nicegui.pages.teams.page_ui import _TeamsPageView
from frontend.ui.nicegui.pages.teams.state import TeamsPageState


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/teams` route."""

    @ui.page("/teams")
    async def teams_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Teams", store=store, api=api)
        with render_container():
            request = getattr(ui.context.client, "request", None)
            with ui.column().classes("w-full gap-1 lp-teams-header"):
                ui.label(subtitle_for(PrimaryPage.TEAMS)).classes("text-sm text-gray-600 lp-teams-subtitle")
                ui.label("Teams and activity").classes("lp-home-title")
                ui.label("Create a team, follow shared activity, and keep reviews moving from one workspace.").classes(
                    "text-sm lp-teams-header-subtitle"
                ).style("color: var(--lp-muted)")
            view = _TeamsPageView(
                controller=TeamsPageController(api=api),
                state=TeamsPageState(),
                username=str((user or {}).get("username") or ""),
                role=str((user or {}).get("role") or ""),
                initial_tab=resolve_activity_tab(request=request),
            )
            view.build()
            await view.refresh_all()
