"""UI sections for the Home stats surfaces."""

from __future__ import annotations

from typing import Any

from nicegui import ui


def contributors_chart_option(rows: list[dict[str, Any]]) -> dict[str, Any]:
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


def render_snapshot_metrics(*, snapshot_stats: dict[str, int]) -> None:
    """Render dashboard snapshot metric cards."""

    def _metric(label: str, value: int, cls: str) -> None:
        with ui.card().classes("lp-card grow"):
            ui.label(label).classes("text-sm text-gray-600")
            ui.label(str(value)).classes(f"text-3xl font-semibold {cls}")

    ui.label("Progress snapshot").classes("text-lg font-semibold mt-2")
    with ui.row().classes("w-full gap-3"):
        _metric("Interested", int(snapshot_stats.get("interested", 0)), "")
        _metric("In progress", int(snapshot_stats.get("in_progress", 0)), "")
        _metric("Completed", int(snapshot_stats.get("completed", 0)), "")


def render_admin_team_section(*, team_stats_by_user: list[dict[str, Any]], contributors: list[dict[str, Any]]) -> None:
    """Render admin-only team stats and contributor chart section."""
    ui.separator()
    ui.label("Team stats by user").classes("text-lg font-semibold")
    if not team_stats_by_user:
        ui.label("No team stats yet. Invite teammates and start sharing learning items to see progress here.").classes(
            "text-sm text-gray-600"
        )
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
    with ui.row().classes("w-full gap-3"):
        with ui.card().classes("lp-card grow min-w-[260px]"):
            ui.label("Top contributors").classes("text-md font-semibold")
            if not contributors:
                ui.label("No contributor activity yet. Shares and reviews will appear here once your team is active.").classes(
                    "text-sm text-gray-600"
                )
            else:
                ui.echart(contributors_chart_option(contributors)).classes("w-full h-56")
