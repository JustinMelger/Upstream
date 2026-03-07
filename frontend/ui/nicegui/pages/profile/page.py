"""Profile page with stats surfaces."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons, render_inline_spinner
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.home.helpers_compat import _top_contributors
from frontend.ui.nicegui.pages.home.state import HomePageState
from frontend.ui.nicegui.pages.home.transitions import begin_home_load, finalize_home_load, should_render_team_section
from frontend.ui.nicegui.pages.profile.controller import ProfilePageController


def _safe_int(value: Any) -> int:
    """Parse int-like value with safe fallback."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _last_updated_copy(*, last_loaded_at: datetime | None) -> str:
    """Return compact relative timestamp text for UI."""
    if last_loaded_at is None:
        return "Last updated: --"
    delta = datetime.now(timezone.utc) - last_loaded_at
    total_seconds = max(0, int(delta.total_seconds()))
    if total_seconds < 60:
        return "Last updated: just now"
    if total_seconds < 3600:
        return f"Last updated: {total_seconds // 60}m ago"
    return f"Last updated: {total_seconds // 3600}h ago"


def _contributors_chart_option(*, contributors: list[dict[str, Any]]) -> dict[str, Any]:
    """Build compact chart config for team contributors."""
    labels = [str(row.get("who") or "") for row in contributors][:6]
    values = [_safe_int(row.get("score")) for row in contributors][:6]
    return {
        "grid": {"left": 24, "right": 18, "top": 16, "bottom": 32},
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"color": "rgba(212,224,238,0.8)"},
            "axisLine": {"lineStyle": {"color": "rgba(186,204,227,0.22)"}},
            "axisTick": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "minInterval": 1,
            "axisLabel": {"color": "rgba(196,210,228,0.68)"},
            "splitLine": {"lineStyle": {"color": "rgba(186,204,227,0.14)"}},
        },
        "series": [
            {
                "type": "bar",
                "data": values,
                "barMaxWidth": 34,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(116,176,228,0.96)"},
                            {"offset": 1, "color": "rgba(79,152,212,0.86)"},
                        ],
                    },
                    "borderRadius": [8, 8, 0, 0],
                },
            }
        ],
        "tooltip": {"trigger": "axis"},
    }


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register `/profile` and `/profile/stats` routes."""

    @ui.page("/profile")
    async def profile_page() -> None:
        ui.navigate.to("/profile/stats")

    @ui.page("/profile/stats")
    async def profile_stats_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        username = str(user.get("username") or "")
        avatar_url = str(user.get("avatar_url") or user.get("profile_image_url") or user.get("image_url") or "").strip()
        avatar_initial = username[:1].upper() if username else "U"
        role = str(user.get("role") or "user")
        is_admin = role == "admin"
        controller = ProfilePageController(api=api)
        last_loaded_at: datetime | None = None
        mode_value = "mine"
        meta_text = ""

        render_shell(title="Profile", store=store, api=api)
        with render_container().classes("lp-profile-scope"):
            ui.label(subtitle_for(PrimaryPage.PROFILE)).classes("text-sm text-gray-600")
            ui.label("Profile analytics").classes("lp-home-title")

            state = HomePageState()

            async def _load_overview() -> None:
                nonlocal last_loaded_at, meta_text
                if state.loading:
                    state.pending_reload = True
                    return
                state.pending_reload = True
                while state.pending_reload:
                    state.pending_reload = False
                    load_start = begin_home_load()
                    state.loading = load_start.loading
                    meta_text = load_start.meta_text
                    dashboard.refresh()

                    ok = False
                    try:
                        bundle = await controller.load_overview(
                            username=username,
                            is_admin=is_admin,
                            mode_value=mode_value,
                        )
                        state.snapshot_stats = dict(bundle.snapshot_stats or {})
                        state.team_stats_by_user = list(bundle.team_stats_by_user or [])
                        last_loaded_at = datetime.now(timezone.utc)
                        ok = True
                    except ApiError as exc:
                        safe_notify(str(exc), type="negative")
                        state.snapshot_stats = {}
                        state.team_stats_by_user = []
                    finally:
                        load_done = finalize_home_load(ok=ok)
                        state.loading = load_done.loading
                        meta_text = load_done.meta_text
                        dashboard.refresh()

            @ui.refreshable
            def dashboard() -> None:
                if state.loading:
                    render_inline_spinner(label="Loading profile stats…")
                    ui.separator()
                    render_card_skeletons(count=3)
                    return

                interested = _safe_int(state.snapshot_stats.get("interested"))
                in_progress = _safe_int(state.snapshot_stats.get("in_progress"))
                completed = _safe_int(state.snapshot_stats.get("completed"))

                with ui.element("section").classes("lp-home-grid-12"):
                    with ui.element("div").classes("lp-home-span-8"):
                        with ui.card().classes("lp-card w-full lp-profile-overview-card"):
                            ui.label("Profile Overview").classes("lp-profile-card-title")
                            with ui.row().classes("items-center gap-3 w-full lp-profile-head"):
                                if avatar_url:
                                    ui.image(avatar_url).classes("lp-profile-avatar-img")
                                else:
                                    ui.label(avatar_initial).classes("lp-profile-avatar-fallback")
                                with ui.column().classes("gap-0"):
                                    ui.label(username).classes("lp-profile-user-name")
                                    ui.label("Learning activity overview").classes("lp-profile-muted")
                            with ui.column().classes("gap-0 mt-1"):
                                ui.label(f"{in_progress} courses in progress").classes("lp-profile-stat-line")
                                ui.label(f"{completed} completed").classes("lp-profile-stat-line")
                                ui.label(f"{interested} interested").classes("lp-profile-stat-line")
                            with ui.row().classes("w-full items-center justify-between"):
                                ui.label(_last_updated_copy(last_loaded_at=last_loaded_at)).classes("lp-profile-muted mt-1")
                                ui.button("Refresh stats", on_click=_load_overview).props("outline dense")

                    with ui.element("div").classes("lp-home-span-4"):
                        with ui.card().classes("lp-card w-full lp-profile-controls-card"):
                            ui.label("Stats View").classes("lp-profile-card-title")
                            if is_admin:
                                mode_control = (
                                    ui.toggle({"mine": "My stats", "team": "Team totals"}, value=mode_value)
                                    .props("unelevated dense no-caps")
                                    .classes("lp-profile-mode-toggle")
                                )

                                async def _on_mode_change(*_args: object) -> None:
                                    nonlocal mode_value
                                    mode_value = str(mode_control.value or "mine")
                                    await _load_overview()

                                mode_control.on("update:model-value", _on_mode_change)
                            ui.button("Refresh", on_click=_load_overview).props("outline dense")
                            ui.label(meta_text).classes("text-xs lp-profile-meta")

                ui.label("Progress Snapshot").classes("lp-profile-section-title")
                ui.label("Your learning activity across courses").classes("lp-profile-muted mb-1")
                with ui.element("section").classes("lp-home-grid-12"):
                    for icon, label, value, context in (
                        ("star", "Interested", interested, "saved items"),
                        ("school", "In progress", in_progress, "active now"),
                        ("check_circle", "Completed", completed, "finished"),
                    ):
                        with ui.element("div").classes("lp-home-span-4"):
                            with ui.card().classes("lp-card w-full lp-profile-metric-card"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon(icon).classes("lp-profile-metric-icon")
                                    ui.label(label).classes("lp-profile-card-title")
                                ui.label(str(value)).classes("lp-profile-metric-value")
                                ui.label(context).classes("lp-profile-muted")

                show_team = should_render_team_section(
                    is_admin=is_admin,
                    mode_value=mode_value,
                )
                if not show_team:
                    return

                contributors = _top_contributors(state.team_stats_by_user, limit=6)
                ui.label("Team Activity").classes("lp-profile-section-title mt-1")
                ui.label("See how your team is progressing").classes("lp-profile-muted mb-1")
                with ui.element("section").classes("lp-home-grid-12"):
                    with ui.element("div").classes("lp-home-span-12"):
                        with ui.card().classes("lp-card w-full lp-profile-chart-card"):
                            ui.label("Top contributors this week").classes("lp-profile-card-title")
                            if not contributors:
                                ui.label("No team contributor data yet. Switch to My stats or invite teammates to get started.").classes(
                                    "lp-profile-muted"
                                )
                            else:
                                ui.echart(_contributors_chart_option(contributors=contributors)).classes("w-full h-64")

                ui.label("Team Learning Stats").classes("lp-profile-section-title mt-1")
                ui.label("Progress distribution across team members").classes("lp-profile-muted mb-1")
                with ui.element("section").classes("lp-home-grid-12"):
                    with ui.element("div").classes("lp-home-span-12"):
                        with ui.card().classes("lp-card w-full lp-profile-table-card"):
                            rows = []
                            for row in list(state.team_stats_by_user or []):
                                who = str(row.get("colleague_id") or "").strip()
                                if not who:
                                    continue
                                rows.append(
                                    {
                                        "user": f"👤 {who}",
                                        "interested": _safe_int(row.get("interested")),
                                        "in_progress": _safe_int(row.get("in_progress")),
                                        "completed": _safe_int(row.get("completed")),
                                    }
                                )
                            if not rows:
                                ui.label("No team stats available yet. Start tracking courses to populate this table.").classes(
                                    "lp-profile-muted"
                                )
                            else:
                                ui.table(
                                    columns=[
                                        {"name": "user", "label": "User", "field": "user", "align": "left"},
                                        {"name": "interested", "label": "Interested", "field": "interested", "align": "right"},
                                        {"name": "in_progress", "label": "In progress", "field": "in_progress", "align": "right"},
                                        {"name": "completed", "label": "Completed", "field": "completed", "align": "right"},
                                    ],
                                    rows=rows,
                                    row_key="user",
                                ).classes("w-full lp-profile-team-table")
            await _load_overview()
            dashboard()
