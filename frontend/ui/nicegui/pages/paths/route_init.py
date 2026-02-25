"""Route/query + intent initialization helpers for Paths page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PathsRouteInit:
    """Resolved initial route state for Paths page."""

    initial_scope: str


def resolve_paths_route_init(*, request: Any) -> PathsRouteInit:
    """Resolve initial scope from query params."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
    initial_scope = "selected" if initial_tab == "selected" else "all"
    return PathsRouteInit(initial_scope=initial_scope)
