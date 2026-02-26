"""Route/query + intent initialization helpers for Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CoursesRouteInit:
    """Resolved initial route state for Courses page."""

    initial_scope: str


def resolve_courses_route_init(*, request: Any) -> CoursesRouteInit:
    """Resolve initial scope from query params."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
    initial_scope = "tracked" if initial_tab == "tracked" else "all"
    return CoursesRouteInit(initial_scope=initial_scope)
