"""Courses-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient


def index_tracking_by_course_id(rows: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Index tracking rows by integer `course_id`."""
    out: dict[int, dict[str, Any]] = {}
    for r in list(rows or []):
        if not isinstance(r, dict):
            continue
        raw = str(r.get("course_id") or "")
        if not raw.isdigit():
            continue
        out[int(raw)] = r
    return out


async def load_courses_and_tracking(
    *,
    api: ApiClient,
    course_params: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    """Load courses and the user's tracking map in one shot."""
    courses_result, tracking_result = await asyncio.gather(
        api.get("/courses", params=course_params or None),
        api.get("/tracking"),
    )
    courses = list(courses_result or [])
    tracking_by_course_id = index_tracking_by_course_id(list(tracking_result or []))
    return courses, tracking_by_course_id


async def load_tracking_map(*, api: ApiClient) -> dict[int, dict[str, Any]]:
    """Load only tracking rows and index them by course id."""
    tracking_result = await api.get("/tracking")
    return index_tracking_by_course_id(list(tracking_result or []))
