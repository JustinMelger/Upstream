"""Route/query initialization for Teams activity-style tabs."""

from __future__ import annotations

from typing import Any


def resolve_activity_tab(*, request: Any) -> str:
    """Resolve initial tab from request query params."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    get = getattr(query_params, "get", None)
    raw = get("tab", "inbox") if callable(get) else "inbox"
    tab = str(raw or "").strip().lower()
    if tab not in {"inbox", "my_teams", "team"}:
        return "inbox"
    return tab
