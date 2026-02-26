"""Paths-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services._indexing import index_by_int_id
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id


def index_rows_by_int_id(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index rows by their integer `id` field."""
    return index_by_int_id(rows, key="id")


def index_courses_by_int_id(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index course rows by integer id (accepts `id` as int or numeric string)."""
    return index_by_int_id(rows, key="id")


def compute_path_progress(
    *,
    detail: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> tuple[int, int, float]:
    """Compute progress for a path detail payload.

    Args:
        detail: Path detail payload including `courses`.
        tracking_by_course_id: Tracking map keyed by course id.

    Returns:
        Tuple of `(completed, total, ratio)`.
    """
    courses = list(detail.get("courses") or []) if isinstance(detail, dict) else []
    total = len(courses)
    completed = 0
    for c in courses:
        if not isinstance(c, dict):
            continue
        raw = c.get("id")
        if raw is None:
            continue
        try:
            cid = int(raw)
        except (TypeError, ValueError):
            continue
        if str((tracking_by_course_id.get(cid) or {}).get("status") or "") == "completed":
            completed += 1
    ratio = (completed / total) if total else 0.0
    return completed, total, ratio


def untracked_path_course_ids(
    *,
    detail: dict[str, Any] | None,
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> list[int]:
    """Return course ids in a path detail payload that are not tracked yet."""
    if not isinstance(detail, dict):
        return []
    out: list[int] = []
    for c in list(detail.get("courses") or []):
        if not isinstance(c, dict):
            continue
        try:
            cid = int(c.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if cid > 0 and cid not in tracking_by_course_id:
            out.append(cid)
    return out


async def select_path_and_seed_tracking(
    *,
    api: ApiClient,
    path_id: int,
    tracking_by_course_id: dict[int, dict[str, Any]],
    cached_detail: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | None]:
    """Select a path and seed missing course tracking rows as interested.

    Returns:
        Tuple of `(seeded_count, detail_payload)`.
    """
    await api.post(f"/paths/{int(path_id)}/select", {})
    detail = cached_detail
    if not isinstance(detail, dict):
        payload = await api.get(f"/paths/{int(path_id)}")
        detail = payload if isinstance(payload, dict) else None

    course_ids = untracked_path_course_ids(detail=detail, tracking_by_course_id=tracking_by_course_id)
    if not course_ids:
        return 0, detail

    results = await asyncio.gather(
        *(api.post("/tracking", {"course_id": int(cid), "status": "interested"}) for cid in course_ids),
        return_exceptions=True,
    )
    seeded = 0
    for row in results:
        if not isinstance(row, Exception):
            seeded += 1
    return seeded, detail


async def unselect_path(*, api: ApiClient, path_id: int) -> bool:
    """Unselect a path for the current user."""
    await api.post(f"/paths/{int(path_id)}/unselect", {})
    return True


async def load_paths_page_data(
    *,
    api: ApiClient,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    """Load `(paths, selected_by_id, courses, course_by_id)` for the Paths page."""
    paths_result, selected_result, courses_result = await asyncio.gather(
        api.get("/paths"),
        api.get("/paths/selected/list"),
        api.get("/courses"),
    )
    paths = list(paths_result or [])
    selected_by_id = index_rows_by_int_id(list(selected_result or []))
    courses = list(courses_result or [])
    course_by_id = index_courses_by_int_id(courses)
    return paths, selected_by_id, courses, course_by_id


async def load_selected_paths(*, api: ApiClient) -> list[dict[str, Any]]:
    """Load the current user's selected paths."""
    return list(await api.get("/paths/selected/list") or [])


async def load_path_recommendation_summaries(*, api: ApiClient, path_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Load recommendation summary items for the given path ids and index them by path id."""
    if not path_ids:
        return {}
    rows = await api.get("/paths/recommendations/summary", params={"path_ids": [int(i) for i in path_ids if int(i) > 0]})
    out: dict[int, dict[str, Any]] = {}
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        try:
            pid = int(row.get("path_id") or 0)
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        out[pid] = row
    return out


def _selected_path_ids(selected_rows: list[dict[str, Any]]) -> list[int]:
    """Extract numeric path ids from selected rows."""
    out: list[int] = []
    for row in selected_rows:
        raw = row.get("id")
        if raw is None:
            continue
        try:
            out.append(int(raw))
        except (TypeError, ValueError):
            continue
    return out


async def _load_selected_path_details(
    *,
    api: ApiClient,
    path_ids: list[int],
) -> dict[int, dict[str, Any]]:
    """Load detail payloads for selected path ids."""
    if not path_ids:
        return {}
    detail_results = await asyncio.gather(*(api.get(f"/paths/{pid}") for pid in path_ids), return_exceptions=True)
    details: dict[int, dict[str, Any]] = {}
    for pid, payload in zip(path_ids, detail_results, strict=False):
        if isinstance(payload, dict):
            details[int(pid)] = payload
    return details


async def load_my_paths_page_data(
    *,
    api: ApiClient,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """Load selected paths, their details, and the user's tracking map.

    Returns:
        Tuple of `(selected_rows, detail_by_path_id, tracking_by_course_id)`.
    """
    selected_result, tracking_result = await asyncio.gather(
        api.get("/paths/selected/list"),
        api.get("/tracking"),
    )
    selected = list(selected_result or [])
    tracking_by_course_id = index_tracking_by_course_id(list(tracking_result or []))
    path_ids = _selected_path_ids(selected)
    details = await _load_selected_path_details(api=api, path_ids=path_ids)

    return selected, details, tracking_by_course_id
