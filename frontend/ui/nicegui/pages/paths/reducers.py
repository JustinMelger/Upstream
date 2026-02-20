"""Pure reducer-style helpers for Paths page filter/list transitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def filter_paths_by_needle(paths: list[dict[str, Any]] | None, needle: str) -> list[dict[str, Any]]:
    """Filter paths by a lower-cased substring match on name/description."""
    if not needle:
        return list(paths or [])
    return [
        p
        for p in list(paths or [])
        if needle in str(p.get("name") or "").lower() or needle in str(p.get("description") or "").lower()
    ]


def apply_scope_and_status(
    *,
    paths: list[dict[str, Any]],
    selected_by_id: dict[int, dict[str, Any]],
    scope_value: str,
    status_value: str,
    path_matches_state: Callable[[int, dict[int, dict[str, Any]], str], bool],
) -> list[dict[str, Any]]:
    """Apply scope/status filters and return the resulting list."""
    shown = list(paths)
    if scope_value == "selected":
        shown = [p for p in shown if int(p.get("id") or 0) in selected_by_id]
    if status_value:
        shown = [p for p in shown if path_matches_state(int(p.get("id") or 0), selected_by_id, status_value)]
    return shown


def sort_paths(
    *,
    paths: list[dict[str, Any]],
    sort_value: str,
    path_review_summary_by_id: dict[int, dict[str, Any]],
    parse_iso_datetime: Callable[[Any], datetime | None],
) -> list[dict[str, Any]]:
    """Sort filtered paths by the active sort key."""
    shown = list(paths)
    if not sort_value:
        return shown
    if sort_value == "name_az":
        return sorted(shown, key=lambda p: str(p.get("name") or "").strip().lower())
    if sort_value == "newest":

        def _created_key(p: dict[str, Any]) -> tuple[datetime, int]:
            dt = parse_iso_datetime(p.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
            return (dt, int(p.get("id") or 0))

        return sorted(shown, key=_created_key, reverse=True)
    if sort_value == "top_rated":

        def _top_rated_key(p: dict[str, Any]) -> tuple[float, int, int]:
            pid = int(p.get("id") or 0)
            row = path_review_summary_by_id.get(pid) or {}
            try:
                avg = float(row.get("avg_rating") or 0.0)
            except (TypeError, ValueError):
                avg = 0.0
            try:
                count = int(row.get("review_count") or 0)
            except (TypeError, ValueError):
                count = 0
            return (avg, count, pid)

        return sorted(shown, key=_top_rated_key, reverse=True)
    if sort_value == "most_reviewed":

        def _most_reviewed_key(p: dict[str, Any]) -> tuple[int, float, int]:
            pid = int(p.get("id") or 0)
            row = path_review_summary_by_id.get(pid) or {}
            try:
                count = int(row.get("review_count") or 0)
            except (TypeError, ValueError):
                count = 0
            try:
                avg = float(row.get("avg_rating") or 0.0)
            except (TypeError, ValueError):
                avg = 0.0
            return (count, avg, pid)

        return sorted(shown, key=_most_reviewed_key, reverse=True)
    return shown


def compute_status_counts(
    *,
    paths: list[dict[str, Any]],
    selected_by_id: dict[int, dict[str, Any]],
    scope_value: str,
    needle: str,
) -> dict[str, int]:
    """Compute tracked/not-tracked counts for facet options."""

    def _passes_scope_and_needle(path_row: dict[str, Any]) -> bool:
        if scope_value == "selected":
            pid = int(path_row.get("id") or 0)
            if pid <= 0 or pid not in selected_by_id:
                return False
        if needle:
            if (
                needle not in str(path_row.get("name") or "").lower()
                and needle not in str(path_row.get("description") or "").lower()
            ):
                return False
        return True

    counts: dict[str, int] = {"not_tracked": 0, "tracked": 0}
    for path_row in list(paths or []):
        if not _passes_scope_and_needle(path_row):
            continue
        pid = int(path_row.get("id") or 0)
        key = "tracked" if pid in selected_by_id else "not_tracked"
        counts[key] = int(counts.get(key, 0)) + 1
    return counts


def build_status_options(*, scope_value: str, counts: dict[str, int]) -> dict[str, str]:
    """Build status facet options for current scope."""
    if scope_value == "selected":
        return {
            "": "Any state",
            "tracked": f"Tracked ({counts.get('tracked', 0)})",
        }
    return {
        "": "Any state",
        "not_tracked": f"Not tracked ({counts.get('not_tracked', 0)})",
        "tracked": f"Tracked ({counts.get('tracked', 0)})",
    }
