"""Dashboard (home page) orchestration for NiceGUI.

This module contains the data-loading "use-case" for the dashboard page. It
exists to keep `pages/home.py` focused on rendering.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


@dataclass(slots=True)
class DashboardData:
    """Container for all dashboard datasets."""

    courses: list[dict[str, Any]]
    paths: list[dict[str, Any]]
    selected_paths: list[dict[str, Any]]
    tracking_rows: list[dict[str, Any]]
    snapshot_stats: dict[str, int]
    team_stats_by_user: list[dict[str, Any]]
    team_recent: list[dict[str, Any]]
    selected_path_details: list[dict[str, Any]]


async def _load_path_detail(*, api: ApiClient, path_id: int) -> dict[str, Any] | None:
    """Load a single path including its courses."""
    try:
        detail = await api.get(f"/paths/{path_id}")
    except Exception:
        return None
    return dict(detail or {}) if isinstance(detail, dict) else None


async def load_dashboard_data(
    *,
    api: ApiClient,
    username: str,
    is_admin: bool,
    mode_value: str,
) -> DashboardData:
    """Load all dashboard data required for the page.

    Args:
        api: API client.
        username: Current username.
        is_admin: Whether the current user is an admin.
        mode_value: Either `"mine"` or `"team"`.

    Returns:
        `DashboardData` containing all datasets needed to render the dashboard.
    """
    tasks: list[asyncio.Future[Any] | asyncio.Task[Any]] = [
        asyncio.create_task(api.get("/courses")),
        asyncio.create_task(api.get("/paths")),
        asyncio.create_task(api.get("/paths/selected/list")),
        asyncio.create_task(api.get("/tracking")),
    ]

    # Stats snapshot
    if is_admin and mode_value == "team":
        tasks.append(asyncio.create_task(api.get("/tracking/stats")))
    else:
        tasks.append(asyncio.create_task(api.get("/tracking/stats", params={"colleague_id": username})))

    # Admin-only panels
    if is_admin:
        tasks.append(asyncio.create_task(api.get("/tracking/stats/users")))
        tasks.append(asyncio.create_task(api.get("/tracking/recent", params={"limit": 5})))

    results = await asyncio.gather(*tasks)
    idx = 0
    courses = list(results[idx] or [])
    idx += 1
    paths = list(results[idx] or [])
    idx += 1
    selected_paths = list(results[idx] or [])
    idx += 1
    tracking_rows = list(results[idx] or [])
    idx += 1
    snapshot_stats = dict(results[idx] or {})
    idx += 1

    team_stats_by_user: list[dict[str, Any]] = []
    team_recent: list[dict[str, Any]] = []
    if is_admin:
        team_stats_by_user = list(results[idx] or [])
        idx += 1
        team_recent = list(results[idx] or [])
        idx += 1

    # Prefetch selected-path details (limit for UX).
    shown = selected_paths[:5]
    details = await asyncio.gather(*[(_load_path_detail(api=api, path_id=int(p.get("id") or 0))) for p in shown])
    selected_path_details = [d for d in details if d]

    return DashboardData(
        courses=courses,
        paths=paths,
        selected_paths=selected_paths,
        tracking_rows=tracking_rows,
        snapshot_stats=snapshot_stats,
        team_stats_by_user=team_stats_by_user,
        team_recent=team_recent,
        selected_path_details=selected_path_details,
    )
