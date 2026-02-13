"""Paths-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


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
