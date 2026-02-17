"""Deterministic filtering helpers used across NiceGUI pages."""

from __future__ import annotations

from typing import Any


def filter_selected_paths(
    selected: list[dict[str, Any]] | None,
    *,
    needle: str,
    status: str,
) -> list[dict[str, Any]]:
    """Filter selected paths by name/description substring and optional status.

    Args:
        selected: Selected path rows (each dict should contain `name` and `status`).
        needle: Substring to match against `name`/`description` (case-insensitive).
        status: Status filter (empty string means "any").

    Returns:
        Filtered list of selected path rows.
    """
    shown = list(selected or [])
    n = needle.strip().lower()
    if n:
        shown = [p for p in shown if n in str(p.get("name") or "").lower() or n in str(p.get("description") or "").lower()]
    s = status.strip()
    if s:
        shown = [p for p in shown if str(p.get("status") or "") == s]
    return shown
