"""Insights page for the NiceGUI frontend."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons, render_inline_spinner
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.home.controller import HomePageController
from frontend.ui.nicegui.pages.home.helpers_compat import _render_snapshot_metrics, _top_contributors
from frontend.ui.nicegui.pages.home.sections import (
    render_admin_team_section,
)
from frontend.ui.nicegui.pages.home.state import HomePageState
from frontend.ui.nicegui.pages.home.transitions import begin_home_load, finalize_home_load, should_render_team_section


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the insights routes.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/")
    async def root_page() -> None:
        """Default app landing route: redirect to My learning."""
        ui.navigate.to("/learning")

    @ui.page("/insights")
    async def home_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        username = str(user.get("username") or "")
        role = str(user.get("role") or "user")
        is_admin = role == "admin"
        controller = HomePageController(api=api)

        render_shell(title="Insights", store=store, api=api)
        with render_container():
            ui.label("Your learning overview and statistics.").classes("text-sm text-gray-600")

            # State
            state = HomePageState()

            meta = ui.label("").classes("text-sm text-gray-600")

            mode = None
            if is_admin:
                mode = ui.radio({"mine": "My stats", "team": "Team totals"}, value="mine")

            async def _load_overview() -> None:
                if state.loading:
                    state.pending_reload = True
                    return
                load_start = begin_home_load()
                state.loading = load_start.loading
                state.pending_reload = False
                refresh_btn.disable()
                meta.text = load_start.meta_text
                dashboard.refresh()

                ok = False
                try:
                    bundle = await controller.load_overview(
                        username=username,
                        is_admin=is_admin,
                        mode_value=str(mode.value) if mode is not None else "mine",
                    )
                    state.snapshot_stats = dict(bundle.snapshot_stats or {})
                    state.team_stats_by_user = list(bundle.team_stats_by_user or [])
                    ok = True
                except Exception as exc:  # ApiError already stringifies nicely, but keep this generic.
                    ui.notify(str(exc), type="negative")
                    state.snapshot_stats = {}
                    state.team_stats_by_user = []
                finally:
                    load_done = finalize_home_load(ok=ok)
                    state.loading = load_done.loading
                    meta.text = load_done.meta_text
                    refresh_btn.enable()
                    dashboard.refresh()
                    if state.pending_reload:
                        state.pending_reload = False
                        await _load_overview()

            @ui.refreshable
            def dashboard() -> None:
                if state.loading:
                    render_inline_spinner(label="Loading dashboard…")
                    ui.separator()
                    render_card_skeletons(count=3)
                    return

                _render_snapshot_metrics(snapshot_stats=state.snapshot_stats)

                # Admin section
                if should_render_team_section(
                    is_admin=is_admin,
                    mode_value=str(mode.value) if mode is not None else "mine",
                ):
                    contributors = _top_contributors(state.team_stats_by_user, limit=5)
                    render_admin_team_section(
                        team_stats_by_user=state.team_stats_by_user,
                        contributors=contributors,
                    )

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load_overview).props("outline")
                ui.label(f"Signed in as {username} ({role})").classes("text-sm text-gray-600")
            meta

            if mode is not None:

                async def _on_mode_change(*_args: object) -> None:
                    await _load_overview()

                mode.on("update:model-value", _on_mode_change)

            await _load_overview()
            dashboard()
