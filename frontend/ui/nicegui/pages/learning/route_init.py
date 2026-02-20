"""Route/query initialization helpers for the Learning page."""

from __future__ import annotations

from typing import Any


def resolve_learning_initial_view(*, request: Any) -> str:
    """Resolve initial `/learning` tab view from query params."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "learning") or "").strip().lower()
    return "shared" if initial_tab == "shared" else "learning"
