"""Route/query + intent initialization helpers for Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CoursesRouteInit:
    """Resolved initial route state for Courses page."""

    initial_scope: str
    initial_course_id: int
    initial_focus_reviews: bool


def resolve_courses_route_init(*, request: Any, storage_intent: dict[str, Any] | None, nav_intent: dict[str, Any] | None) -> CoursesRouteInit:
    """Resolve initial scope/course/dialog mode from query params and intents."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
    initial_scope = "tracked" if initial_tab == "tracked" else "all"

    initial_course_id_raw = str(getattr(query_params, "get", lambda _k, _d=None: _d)("course_id", "") or "").strip()
    try:
        initial_course_id = int(initial_course_id_raw) if initial_course_id_raw else 0
    except (TypeError, ValueError):
        initial_course_id = 0

    initial_view_mode = str(getattr(query_params, "get", lambda _k, _d=None: _d)("view", "") or "").strip().lower()
    initial_focus_reviews = initial_view_mode == "reviews"

    for intent in [storage_intent, nav_intent]:
        if not isinstance(intent, dict):
            continue
        if initial_course_id <= 0:
            try:
                initial_course_id = int(intent.get("course_id") or 0)
            except (TypeError, ValueError):
                initial_course_id = 0
        if initial_view_mode not in {"full", "reviews"}:
            initial_focus_reviews = str(intent.get("view") or "").strip().lower() == "reviews"

    return CoursesRouteInit(
        initial_scope=initial_scope,
        initial_course_id=int(initial_course_id),
        initial_focus_reviews=bool(initial_focus_reviews),
    )


def intent_matches_course(intent: dict[str, Any] | None, course_id: int) -> bool:
    """Return whether an intent targets the opened course id."""
    if not isinstance(intent, dict):
        return False
    try:
        return int(intent.get("course_id") or 0) == int(course_id)
    except (TypeError, ValueError):
        return False
