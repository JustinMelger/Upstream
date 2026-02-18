"""Insights page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons, render_inline_spinner
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.dashboard_service import load_dashboard_data


def _top_contributors(rows: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    """Rank teammates by a weighted activity score."""
    ranked: list[dict[str, Any]] = []
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        who = str(row.get("colleague_id") or "").strip()
        if not who:
            continue
        try:
            interested = int(row.get("interested") or 0)
            in_progress = int(row.get("in_progress") or 0)
            completed = int(row.get("completed") or 0)
        except (TypeError, ValueError):
            continue
        score = (completed * 3) + (in_progress * 2) + interested
        ranked.append(
            {
                "who": who,
                "interested": interested,
                "in_progress": in_progress,
                "completed": completed,
                "score": score,
            }
        )
    return sorted(
        ranked,
        key=lambda r: (int(r.get("score") or 0), int(r.get("completed") or 0), str(r.get("who") or "")),
        reverse=True,
    )[:limit]


def _contributors_chart_option(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build ECharts option for top contributors."""
    labels = [str(r.get("who") or "") for r in rows][:5]
    values = [int(r.get("score") or 0) for r in rows][:5]
    return {
        "grid": {"left": 40, "right": 20, "top": 10, "bottom": 45},
        "xAxis": {"type": "category", "data": labels, "axisLabel": {"rotate": 35, "interval": 0}},
        "yAxis": {"type": "value", "minInterval": 1},
        "series": [
            {
                "type": "bar",
                "data": values,
                "itemStyle": {"color": "#4ea8ff"},
                "label": {"show": True, "position": "top", "color": "#dbe8ff"},
            }
        ],
        "tooltip": {"trigger": "item"},
    }


def _render_snapshot_metrics(*, snapshot_stats: dict[str, int]) -> None:
    """Render the three dashboard snapshot metric cards."""

    def _metric(label: str, value: int, cls: str) -> None:
        with ui.card().classes("lp-card grow"):
            ui.label(label).classes("text-sm text-gray-600")
            ui.label(str(value)).classes(f"text-3xl font-semibold {cls}")

    ui.label("Progress snapshot").classes("text-lg font-semibold mt-2")
    with ui.row().classes("w-full gap-3"):
        _metric("Interested", int(snapshot_stats.get("interested", 0)), "")
        _metric("In progress", int(snapshot_stats.get("in_progress", 0)), "")
        _metric("Completed", int(snapshot_stats.get("completed", 0)), "")


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

        render_shell(title="Insights", store=store, api=api)
        with render_container():
            ui.label("Your learning overview and statistics.").classes("text-sm text-gray-600")

            # State
            snapshot_stats: dict[str, int] = {}
            team_stats_by_user: list[dict[str, Any]] = []

            meta = ui.label("").classes("text-sm text-gray-600")
            loading = False

            @guard_ui_action(title="Update status failed")
            async def _mark_completed(course_id: int) -> None:
                await api.post("/tracking", {"course_id": course_id, "status": "completed"})
                ui.notify("Marked completed", type="positive")
                await _load_overview()

            @guard_ui_action(title="Update status failed")
            async def _mark_in_progress(course_id: int) -> None:
                await api.post("/tracking", {"course_id": course_id, "status": "in_progress"})
                ui.notify("Marked in progress", type="positive")
                await _load_overview()

            mode = None
            if is_admin:
                mode = ui.radio({"mine": "My stats", "team": "Team totals"}, value="mine")

            async def _load_overview() -> None:
                nonlocal snapshot_stats, team_stats_by_user
                nonlocal loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
                dashboard.refresh()

                try:
                    data = await load_dashboard_data(
                        api=api,
                        username=username,
                        is_admin=is_admin,
                        mode_value=str(mode.value) if mode is not None else "mine",
                    )
                    snapshot_stats = dict(data.snapshot_stats)
                    team_stats_by_user = list(data.team_stats_by_user)

                    dashboard.refresh()
                    meta.text = "Updated"
                except Exception as exc:  # ApiError already stringifies nicely, but keep this generic.
                    ui.notify(str(exc), type="negative")
                    snapshot_stats = {}
                    team_stats_by_user = []
                    dashboard.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    refresh_btn.enable()
                    dashboard.refresh()

            @ui.refreshable
            def dashboard() -> None:
                if loading:
                    render_inline_spinner(label="Loading dashboard…")
                    ui.separator()
                    render_card_skeletons(count=3)
                    return

                _render_snapshot_metrics(snapshot_stats=snapshot_stats)

                # Admin section
                if is_admin:
                    ui.separator()
                    ui.label("Team stats by user").classes("text-lg font-semibold")
                    if not team_stats_by_user:
                        ui.label("No user stats yet.").classes("text-sm text-gray-600")
                    else:
                        ui.table(
                            columns=[
                                {"name": "colleague_id", "label": "User", "field": "colleague_id"},
                                {"name": "interested", "label": "Interested", "field": "interested"},
                                {"name": "in_progress", "label": "In progress", "field": "in_progress"},
                                {"name": "completed", "label": "Completed", "field": "completed"},
                            ],
                            rows=team_stats_by_user,
                            row_key="colleague_id",
                        ).classes("w-full")

                    ui.label("Team visibility dashboard").classes("text-lg font-semibold mt-4")
                    contributors = _top_contributors(team_stats_by_user, limit=5)
                    with ui.row().classes("w-full gap-3"):
                        with ui.card().classes("lp-card grow min-w-[260px]"):
                            ui.label("Top contributors").classes("text-md font-semibold")
                            if not contributors:
                                ui.label("No contributor data yet.").classes("text-sm text-gray-600")
                            else:
                                ui.echart(_contributors_chart_option(contributors)).classes("w-full h-56")

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load_overview).props("outline")
                ui.label(f"Signed in as {username} ({role})").classes("text-sm text-gray-600")
            meta

            if mode is not None:

                async def _on_mode_change(*_args: Any) -> None:
                    await _load_overview()

                mode.on("update:model-value", _on_mode_change)

            await _load_overview()
            dashboard()
