"""AI Curator orchestration for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.pages.ai_curator.ui_glue import (
    build_path_payload,
    draft_course_to_create_payload,
    normalize_draft_courses,
)


async def generate_plan(*, api: ApiClient, goal: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Generate draft path/courses from goal."""
    plan = await api.post("/ai/plan", {"goal": str(goal or "").strip()})
    path = dict(plan.get("path") or {}) if isinstance(plan, dict) else {}
    courses = normalize_draft_courses(list(plan.get("courses") or []) if isinstance(plan, dict) else [])
    return path, courses


async def apply_plan(
    *,
    api: ApiClient,
    draft_courses: list[dict[str, Any]],
    path_name: str,
    path_description: str,
    select_for_me: bool,
) -> int:
    """Create courses/path from editable draft and optionally select path."""
    created_ids: list[int] = []
    for row in list(draft_courses or []):
        payload = draft_course_to_create_payload(row)
        created = await api.post("/courses", payload)
        course_id = int((created or {}).get("id") or 0)
        if course_id <= 0:
            raise RuntimeError("invalid_created_course_id")
        created_ids.append(course_id)

    path_payload = build_path_payload(name=path_name, description=path_description, course_ids=created_ids)
    created_path = await api.post("/paths", path_payload)
    path_id = int((created_path or {}).get("id") or 0)
    if path_id <= 0:
        raise RuntimeError("invalid_created_path_id")
    if select_for_me and path_id > 0:
        await api.post(f"/paths/{path_id}/select", {})
    return path_id
