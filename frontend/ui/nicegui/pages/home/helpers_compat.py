"""Compatibility helper functions kept for legacy tests/importers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.pages.home.sections import contributors_chart_option, render_snapshot_metrics
from frontend.ui.nicegui.services.dashboard_service import _tracking_map as _tracking_map_service


def _parse_iso_ts(value: Any) -> datetime | None:
    """Compatibility wrapper kept for helper tests."""
    return parse_iso_datetime(value)


def _tracking_map(tracking_rows: list[dict[str, Any]]) -> dict[int, str]:
    """Compatibility wrapper around dashboard tracking mapping."""
    return _tracking_map_service(tracking_rows)


def _ids_by_status(tracking: dict[int, str]) -> tuple[list[int], list[int], list[int]]:
    """Split tracked course ids by status."""
    interested = [int(cid) for cid, status in tracking.items() if str(status or "") == "interested"]
    in_progress = [int(cid) for cid, status in tracking.items() if str(status or "") == "in_progress"]
    completed = [int(cid) for cid, status in tracking.items() if str(status or "") == "completed"]
    return interested, in_progress, completed


def _recent_tracking(rows: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    """Sort tracking rows by updated_at descending, skipping invalid timestamps."""
    parsed: list[tuple[datetime, dict[str, Any]]] = []
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        dt = _parse_iso_ts(row.get("updated_at"))
        if not dt:
            continue
        parsed.append((dt, row))
    parsed.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in parsed[: max(0, int(limit))]]


def _recent_courses(courses: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    """Sort courses by created_at descending, skipping invalid timestamps."""
    parsed: list[tuple[datetime, dict[str, Any]]] = []
    for course in list(courses or []):
        if not isinstance(course, dict):
            continue
        dt = _parse_iso_ts(course.get("created_at"))
        if not dt:
            continue
        parsed.append((dt, course))
    parsed.sort(key=lambda item: item[0], reverse=True)
    return [course for _, course in parsed[: max(0, int(limit))]]


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
    """Compatibility wrapper for contributors chart option helper."""
    return contributors_chart_option(rows)


def _render_snapshot_metrics(*, snapshot_stats: dict[str, int]) -> None:
    """Compatibility wrapper for snapshot metric section."""
    render_snapshot_metrics(snapshot_stats=snapshot_stats)
