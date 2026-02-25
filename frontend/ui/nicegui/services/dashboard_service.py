"""Dashboard (home page) orchestration for NiceGUI.

This module contains the data-loading "use-case" for the dashboard page. It
exists to keep `pages/home.py` focused on rendering.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError


logger = logging.getLogger(__name__)


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
    team_tracking_rows: list[dict[str, Any]]


def _index_review_summary(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index review summary rows by course_id."""
    out: dict[int, dict[str, Any]] = {}
    for r in list(rows or []):
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
    except ApiError as exc:
        logger.warning(
            "Dashboard review summaries unavailable",
            extra={"status_code": int(exc.status_code), "course_count": len(unique)},
        )
        return {}
    return _index_review_summary(list(rows or []))


async def _load_path_detail(*, api: ApiClient, path_id: int) -> dict[str, Any] | None:
    """Load a single path including its courses."""
    try:
        detail = await api.get(f"/paths/{path_id}")
    except ApiError as exc:
        logger.warning(
            "Dashboard selected path detail unavailable",
            extra={"status_code": int(exc.status_code), "path_id": int(path_id)},
        )
        return None
    return dict(detail or {}) if isinstance(detail, dict) else None


def _collect_colleague_ids(team_stats_by_user: list[dict[str, Any]]) -> list[str]:
    """Collect unique colleague ids preserving first-seen order."""
    colleague_ids: list[str] = []
    seen_ids: set[str] = set()
    for row in team_stats_by_user:
        who = str(row.get("colleague_id") or "").strip()
        if not who or who in seen_ids:
            continue
        seen_ids.add(who)
        colleague_ids.append(who)
    return colleague_ids


async def _load_team_tracking_rows(*, api: ApiClient, colleague_ids: list[str]) -> list[dict[str, Any]]:
    """Load tracking rows for all colleagues, skipping failed payloads."""
    if not colleague_ids:
        return []
    payloads = await asyncio.gather(
        *(api.get("/tracking", params={"colleague_id": who}) for who in colleague_ids),
        return_exceptions=True,
    )
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        if not isinstance(payload, list):
            continue
        rows.extend(dict(row) for row in payload if isinstance(row, dict))
    return rows


async def _load_admin_panels(*, api: ApiClient) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load admin-only dashboard panels."""
    team_stats_by_user, team_recent = await asyncio.gather(
        api.get("/tracking/stats/users"),
        api.get("/tracking/recent", params={"limit": 100}),
    )
    return list(team_stats_by_user or []), list(team_recent or [])


def _snapshot_stats_task(*, api: ApiClient, username: str, is_admin: bool, mode_value: str) -> asyncio.Task[Any]:
    """Create task loading dashboard snapshot stats for the selected mode."""
    if is_admin and mode_value == "team":
        return asyncio.create_task(api.get("/tracking/stats"))
    return asyncio.create_task(api.get("/tracking/stats", params={"colleague_id": username}))


async def _load_base_dashboard_lists(
    *, api: ApiClient, username: str, is_admin: bool, mode_value: str
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, int],
]:
    """Load always-required dashboard datasets."""
    courses, paths, selected_paths, tracking_rows, snapshot_stats = await asyncio.gather(
        api.get("/courses"),
        api.get("/paths"),
        api.get("/paths/selected/list"),
        api.get("/tracking"),
        _snapshot_stats_task(api=api, username=username, is_admin=is_admin, mode_value=mode_value),
    )
    return (
        list(courses or []),
        list(paths or []),
        list(selected_paths or []),
        list(tracking_rows or []),
        dict(snapshot_stats or {}),
    )


async def _load_selected_path_details(*, api: ApiClient, selected_paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load details for the first selected paths used on dashboard."""
    shown = selected_paths[:5]
    details = await asyncio.gather(*[(_load_path_detail(api=api, path_id=int(p.get("id") or 0))) for p in shown])
    return [d for d in details if d]


def _collect_next_up_ids(
    *,
    selected_path_details: list[dict[str, Any]],
    tracking: dict[int, str],
) -> list[int]:
    """Collect first non-completed course per selected path."""
    next_up_ids: list[int] = []
    for detail in selected_path_details:
        for course in list(detail.get("courses") or []):
            try:
                cid = int(course.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid > 0 and tracking.get(cid, "") != "completed":
                next_up_ids.append(cid)
                break
    return next_up_ids


def _collect_recent_course_ids(courses: list[dict[str, Any]]) -> list[int]:
    """Collect up to 3 recent course ids."""
    ids: list[int] = []
    for course in courses[:3]:
        try:
            ids.append(int(course.get("id") or 0))
        except (TypeError, ValueError):
            continue
    return ids


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
    courses, paths, selected_paths, tracking_rows, snapshot_stats = await _load_base_dashboard_lists(
        api=api,
        username=username,
        is_admin=is_admin,
        mode_value=mode_value,
    )

    team_stats_by_user: list[dict[str, Any]] = []
    team_recent: list[dict[str, Any]] = []
    team_tracking_rows: list[dict[str, Any]] = []
    if is_admin:
        team_stats_by_user, team_recent = await _load_admin_panels(api=api)
        team_tracking_rows = await _load_team_tracking_rows(
            api=api,
            colleague_ids=_collect_colleague_ids(team_stats_by_user),
        )

    selected_path_details = await _load_selected_path_details(api=api, selected_paths=selected_paths)

    tracking = _tracking_map(tracking_rows)
    in_progress_ids = [cid for cid, st in tracking.items() if st == "in_progress"]
    next_up_ids = _collect_next_up_ids(selected_path_details=selected_path_details, tracking=tracking)
    recent_course_ids = _collect_recent_course_ids(courses)

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
        team_tracking_rows=team_tracking_rows,
    )
