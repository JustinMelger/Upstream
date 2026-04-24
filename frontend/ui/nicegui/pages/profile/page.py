"""Profile page with stats surfaces."""

from __future__ import annotations

from dataclasses import dataclass
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
from frontend.ui.nicegui.pages.shared_stats.controller import SharedStatsController
from frontend.ui.nicegui.pages.shared_stats.helpers import top_contributors
from frontend.ui.nicegui.pages.shared_stats.state import SharedStatsState
from frontend.ui.nicegui.pages.shared_stats.transitions import (
    begin_shared_stats_load,
    finalize_shared_stats_load,
    should_render_team_stats,
)


@dataclass(slots=True)
class ProfileStatsPageContext:
    """Mutable view context for the profile stats page."""

    username: str
    avatar_url: str
    avatar_initial: str
    is_admin: bool
    controller: SharedStatsController
    state: SharedStatsState
    last_loaded_at: datetime | None = None
    mode_value: str = "mine"
    meta_text: str = ""


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


async def _load_profile_overview(*, ctx: ProfileStatsPageContext, dashboard: Any) -> None:
    """Load or reload profile overview data and refresh the dashboard."""
    if ctx.state.loading:
        ctx.state.pending_reload = True
        return
    ctx.state.pending_reload = True
    while ctx.state.pending_reload:
        ctx.state.pending_reload = False
        load_start = begin_shared_stats_load()
        ctx.state.loading = load_start.loading
        ctx.meta_text = load_start.meta_text
        dashboard.refresh()

        ok = False
        try:
            bundle = await ctx.controller.load_overview(
                username=ctx.username,
                is_admin=ctx.is_admin,
                mode_value=ctx.mode_value,
            )
            ctx.state.snapshot_stats = dict(bundle.snapshot_stats or {})
            ctx.state.team_stats_by_user = list(bundle.team_stats_by_user or [])
            ctx.last_loaded_at = datetime.now(timezone.utc)
            ok = True
        except ApiError as exc:
            safe_notify(str(exc), type="negative")
            ctx.state.snapshot_stats = {}
            ctx.state.team_stats_by_user = []
        finally:
            load_done = finalize_shared_stats_load(ok=ok)
            ctx.state.loading = load_done.loading
            ctx.meta_text = load_done.meta_text
            dashboard.refresh()


def _render_profile_summary_section(*, ctx: ProfileStatsPageContext, on_refresh: Any) -> None:
    """Render the compact profile summary rail."""
    interested = _safe_int(ctx.state.snapshot_stats.get("interested"))
    in_progress = _safe_int(ctx.state.snapshot_stats.get("in_progress"))
    completed = _safe_int(ctx.state.snapshot_stats.get("completed"))

    with ui.card().classes("lp-card w-full lp-profile-summary-card"):
        with ui.row().classes("w-full items-start justify-between gap-4 no-wrap lp-profile-summary-rail"):
            with ui.row().classes("items-center gap-3 lp-profile-head"):
                if ctx.avatar_url:
                    ui.image(ctx.avatar_url).classes("lp-profile-avatar-img")
                else:
                    ui.label(ctx.avatar_initial).classes("lp-profile-avatar-fallback")
                with ui.column().classes("gap-0"):
                    ui.label(ctx.username).classes("lp-profile-user-name")
                    ui.label("Personal and team learning totals").classes("lp-profile-muted")
                    ui.label(
                        f"{in_progress} in progress  ·  {completed} completed  ·  {interested} interested"
                    ).classes("lp-profile-stat-line")
            with ui.column().classes("items-end gap-2 lp-profile-summary-meta"):
                ui.label(_last_updated_copy(last_loaded_at=ctx.last_loaded_at)).classes("lp-profile-muted")
                if ctx.meta_text:
                    ui.label(ctx.meta_text).classes("text-xs lp-profile-meta")
                ui.button("Refresh stats", on_click=on_refresh).props("outline dense")


def _render_mode_toggle(*, ctx: ProfileStatsPageContext, on_refresh: Any) -> None:
    """Render the admin stats mode toggle."""
    if not ctx.is_admin:
        return
    mode_control = (
        ui.toggle({"mine": "My stats", "team": "Team totals"}, value=ctx.mode_value)
        .props("unelevated dense no-caps")
        .classes("lp-profile-mode-toggle")
    )

    async def _on_mode_change(*_args: object) -> None:
        ctx.mode_value = str(mode_control.value or "mine")
        await on_refresh()

    mode_control.on("update:model-value", _on_mode_change)


def _render_profile_progress_snapshot(*, ctx: ProfileStatsPageContext) -> None:
    """Render the profile progress snapshot cards."""
    interested = _safe_int(ctx.state.snapshot_stats.get("interested"))
    in_progress = _safe_int(ctx.state.snapshot_stats.get("in_progress"))
    completed = _safe_int(ctx.state.snapshot_stats.get("completed"))
    ui.label("Progress Snapshot").classes("lp-profile-section-title")
    ui.label("Your learning activity across courses").classes("lp-profile-muted mb-1")
    with ui.element("section").classes("lp-home-grid-12"):
        for icon, label, value, summary in (
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
                    ui.label(summary).classes("lp-profile-muted")


def _build_team_stat_rows(*, team_stats_by_user: list[dict[str, Any]]) -> list[dict[str, object]]:
    """Normalize team stats rows for the profile table."""
    rows: list[dict[str, object]] = []
    for row in list(team_stats_by_user or []):
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
    return rows


def _render_profile_team_sections(*, ctx: ProfileStatsPageContext) -> None:
    """Render team activity chart and stats table when team mode is active."""
    if not should_render_team_stats(is_admin=ctx.is_admin, mode_value=ctx.mode_value):
        return

    contributors = top_contributors(ctx.state.team_stats_by_user, limit=6)
    ui.label("Team Activity").classes("lp-profile-section-title mt-1")
    ui.label("See how your team is progressing across contributors and totals.").classes("lp-profile-muted mb-1")
    with ui.element("section").classes("lp-home-grid-12"):
        with ui.element("div").classes("lp-home-span-12"):
            with ui.card().classes("lp-card w-full lp-profile-chart-card"):
                ui.label("Top contributors this week").classes("lp-profile-card-title")
                ui.label("Recent contribution momentum across your workspace.").classes("lp-profile-card-subtitle")
                if not contributors:
                    ui.label(
                        "No team contributor data yet. Open Teams to invite teammates or switch to My stats to review your own progress."
                    ).classes("lp-profile-muted")
                else:
                    ui.echart(_contributors_chart_option(contributors=contributors)).classes("w-full h-64")

    with ui.element("section").classes("lp-home-grid-12"):
        with ui.element("div").classes("lp-home-span-12"):
            with ui.card().classes("lp-card w-full lp-profile-table-card"):
                ui.label("Team learning totals").classes("lp-profile-card-title")
                ui.label("Progress distribution across team members.").classes("lp-profile-card-subtitle")
                rows = _build_team_stat_rows(team_stats_by_user=ctx.state.team_stats_by_user)
                if not rows:
                    ui.label(
                        "No team stats available yet. Open Teams to build your workspace or switch to My stats to review your own activity."
                    ).classes("lp-profile-muted")
                    return
                ui.table(
                    columns=[
                        {"name": "user", "label": "User", "field": "user", "align": "left"},
                        {"name": "interested", "label": "Interested", "field": "interested", "align": "right"},
                        {
                            "name": "in_progress",
                            "label": "In progress",
                            "field": "in_progress",
                            "align": "right",
                        },
                        {"name": "completed", "label": "Completed", "field": "completed", "align": "right"},
                    ],
                    rows=rows,
                    row_key="user",
                ).classes("w-full lp-profile-team-table")


async def _render_profile_stats_page(*, store: SessionStore, api: ApiClient) -> None:
    """Render the profile stats route."""
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    ctx = ProfileStatsPageContext(
        username=username,
        avatar_url=str(user.get("avatar_url") or user.get("profile_image_url") or user.get("image_url") or "").strip(),
        avatar_initial=username[:1].upper() if username else "U",
        is_admin=str(user.get("role") or "user") == "admin",
        controller=SharedStatsController(api=api),
        state=SharedStatsState(),
    )

    render_shell(title="Profile", store=store, api=api)
    with render_container().classes("lp-profile-scope"):
        ui.label(subtitle_for(PrimaryPage.PROFILE)).classes("text-sm text-gray-600")
        ui.label("Learning stats").classes("lp-home-title")

        @ui.refreshable
        def dashboard() -> None:
            if ctx.state.loading:
                render_inline_spinner(label="Loading profile stats…")
                ui.separator()
                render_card_skeletons(count=3)
                return

            _render_mode_toggle(
                ctx=ctx,
                on_refresh=lambda: _load_profile_overview(ctx=ctx, dashboard=dashboard),
            )
            ui.element("div").classes("h-3")
            _render_profile_summary_section(
                ctx=ctx,
                on_refresh=lambda: _load_profile_overview(ctx=ctx, dashboard=dashboard),
            )
            ui.element("div").classes("h-2")
            _render_profile_progress_snapshot(ctx=ctx)
            _render_profile_team_sections(ctx=ctx)

        await _load_profile_overview(ctx=ctx, dashboard=dashboard)
        dashboard()


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register `/profile` and `/profile/stats` routes."""

    @ui.page("/profile")
    async def profile_page() -> None:
        ui.navigate.to("/profile/stats")

    @ui.page("/profile/stats")
    async def profile_stats_page() -> None:
        await _render_profile_stats_page(store=store, api=api)
