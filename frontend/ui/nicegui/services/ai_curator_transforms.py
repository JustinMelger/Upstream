"""Pure transform helpers for AI Curator service/page flows."""

from __future__ import annotations

from typing import Any, Sequence


def normalize_draft_courses(rows: Sequence[object] | None) -> list[dict[str, Any]]:
    """Normalize draft course rows into editable dicts."""
    out: list[dict[str, Any]] = []
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "title": str(row.get("title") or "").strip(),
                "description": str(row.get("description") or "").strip(),
                "provider": str(row.get("provider") or "").strip(),
                "category": str(row.get("category") or "").strip(),
                "level": str(row.get("level") or "").strip(),
                "duration_hours": row.get("duration_hours"),
                "url": str(row.get("url") or "").strip(),
            }
        )
    return out


def draft_course_to_create_payload(course: dict[str, Any]) -> dict[str, Any]:
    """Map a draft course row into `/courses` create payload."""
    return {
        "title": str(course.get("title") or "").strip(),
        "description": str(course.get("description") or "").strip(),
        "provider": str(course.get("provider") or "").strip(),
        "category": str(course.get("category") or "").strip(),
        "level": str(course.get("level") or "").strip(),
        "duration_hours": course.get("duration_hours"),
        "url": str(course.get("url") or "").strip(),
    }


def build_path_payload(*, name: str, description: str, course_ids: list[int]) -> dict[str, Any]:
    """Build `/paths` create payload from edited draft fields."""
    ordered_ids = [int(cid) for cid in list(course_ids or []) if int(cid) > 0]
    return {
        "name": str(name or "").strip(),
        "description": str(description or "").strip(),
        "items": [{"type": "course", "id": int(course_id), "position": idx} for idx, course_id in enumerate(ordered_ids)],
    }
