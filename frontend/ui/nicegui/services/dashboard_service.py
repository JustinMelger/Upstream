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
    review_summary_by_course_id: dict[int, dict[str, Any]]


def _index_review_summary(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index review summary rows by course_id."""
    out: dict[int, dict[str, Any]] = {}
    for r in list(rows or []):
        if not isinstance(r, dict):
            continue
        try:
            cid = int(r.get("course_id") or 0)
        except (TypeError, ValueError):
            continue
        if cid <= 0:
            continue
        out[cid] = r
    return out


def _tracking_map(tracking_rows: list[dict[str, Any]]) -> dict[int, str]:
    """Build a mapping of course_id -> status."""
    out: dict[int, str] = {}
    for r in list(tracking_rows or []):
        try:
            cid = int(r.get("course_id") or 0)
        except (TypeError, ValueError):
            continue
        if cid <= 0:
            continue
        out[cid] = str(r.get("status") or "")
    return out


async def _load_review_summaries(*, api: ApiClient, course_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Load review summary rows for the given course ids."""
    unique: list[int] = []
    seen: set[int] = set()
    for cid in list(course_ids or []):
        try:
            cid_i = int(cid)
        except (TypeError, ValueError):
            continue
        if cid_i <= 0 or cid_i in seen:
            continue
        seen.add(cid_i)
        unique.append(cid_i)
    if not unique:
        return {}
    try:
        rows = await api.get("/courses/reviews/summary", params={"course_ids": unique})
    except Exception:
        return {}
    return _index_review_summary(list(rows or []))


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

    tracking = _tracking_map(tracking_rows)
    in_progress_ids = [cid for cid, st in tracking.items() if st == "in_progress"]
    next_up_ids: list[int] = []
    for detail in selected_path_details:
        courses_in_path = list(detail.get("courses") or [])
        for c in courses_in_path:
            try:
                cid = int(c.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid <= 0:
                continue
            if tracking.get(cid, "") != "completed":
                next_up_ids.append(cid)
                break

    recent_course_ids: list[int] = []
    for c in courses[:3]:
        try:
            recent_course_ids.append(int(c.get("id") or 0))
        except (TypeError, ValueError):
            continue

    summary_ids = list({cid for cid in (in_progress_ids[:3] + next_up_ids[:5] + recent_course_ids) if int(cid) > 0})
    review_summary_by_course_id = await _load_review_summaries(api=api, course_ids=summary_ids)

    return DashboardData(
        courses=courses,
        paths=paths,
        selected_paths=selected_paths,
        tracking_rows=tracking_rows,
        snapshot_stats=snapshot_stats,
        team_stats_by_user=team_stats_by_user,
        team_recent=team_recent,
        selected_path_details=selected_path_details,
        review_summary_by_course_id=review_summary_by_course_id,
    )
