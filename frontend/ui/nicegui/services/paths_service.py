"""Paths-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id


def index_rows_by_int_id(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index rows by their integer `id` field."""
    out: dict[int, dict[str, Any]] = {}
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        raw = row.get("id")
        if raw is None:
            continue
        try:
            out[int(raw)] = row
        except (TypeError, ValueError):
            continue
    return out


def index_courses_by_int_id(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index course rows by integer id (accepts `id` as int or numeric string)."""
    out: dict[int, dict[str, Any]] = {}
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        raw = row.get("id")
        if raw is None:
            continue
        try:
            out[int(raw)] = row
        except (TypeError, ValueError):
            continue
    return out


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

    path_ids: list[int] = []
    for row in selected:
        if not isinstance(row, dict):
            continue
        raw = row.get("id")
        if raw is None:
            continue
        try:
            path_ids.append(int(raw))
        except (TypeError, ValueError):
            continue

    details: dict[int, dict[str, Any]] = {}
    if path_ids:
        # Fetch path details in parallel so the UI can compute progress-at-a-glance.
        detail_results = await asyncio.gather(*(api.get(f"/paths/{pid}") for pid in path_ids), return_exceptions=True)
        for pid, payload in zip(path_ids, detail_results, strict=False):
            if isinstance(payload, Exception):
                continue
            if isinstance(payload, dict):
                details[int(pid)] = payload

    return selected, details, tracking_by_course_id
