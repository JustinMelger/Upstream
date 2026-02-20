"""Route/query + intent initialization helpers for Paths page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PathsRouteInit:
    """Resolved initial route state for Paths page."""

    initial_scope: str
    initial_path_id: int
    initial_dialog_mode: str


def resolve_paths_route_init(
    *,
    request: Any,
    storage_intent: dict[str, Any] | None,
    nav_intent: dict[str, Any] | None,
    normalize_view_mode: Any,
) -> PathsRouteInit:
    """Resolve initial scope/path/dialog mode from query params and intents."""
    query_params = getattr(request, "query_params", {}) if request is not None else {}
    initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
    initial_scope = "selected" if initial_tab == "selected" else "all"

    initial_path_id_raw = str(getattr(query_params, "get", lambda _k, _d=None: _d)("path_id", "") or "").strip()
    try:
        initial_path_id = int(initial_path_id_raw) if initial_path_id_raw else 0
    except (TypeError, ValueError):
        initial_path_id = 0

    initial_view_mode = str(getattr(query_params, "get", lambda _k, _d=None: _d)("view", "") or "").strip().lower()
    initial_dialog_mode = normalize_view_mode(initial_view_mode)

    for intent in [storage_intent, nav_intent]:
        if not isinstance(intent, dict):
            continue
        if initial_path_id <= 0:
            try:
                initial_path_id = int(intent.get("path_id") or 0)
            except (TypeError, ValueError):
                initial_path_id = 0
        if initial_view_mode not in {"full", "reviews"}:
            initial_dialog_mode = normalize_view_mode(intent.get("view"))

    return PathsRouteInit(
        initial_scope=initial_scope,
        initial_path_id=int(initial_path_id),
        initial_dialog_mode=str(initial_dialog_mode),
    )


def intent_matches_path(intent: dict[str, Any] | None, path_id: int) -> bool:
    """Return whether an intent targets the opened path id."""
    if not isinstance(intent, dict):
        return False
    try:
        return int(intent.get("path_id") or 0) == int(path_id)
    except (TypeError, ValueError):
        return False
