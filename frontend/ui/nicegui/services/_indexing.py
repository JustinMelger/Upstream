"""Small indexing helpers for NiceGUI service orchestration."""

from __future__ import annotations

from typing import Any


def index_by_int_id(rows: list[dict[str, Any]] | None, *, key: str = "id") -> dict[int, dict[str, Any]]:
    """Index rows by integer value of `key`.

    Args:
        rows: List of dict payloads.
        key: Field name to index by.

    Returns:
        Mapping of int(key) -> row.
    """
    out: dict[int, dict[str, Any]] = {}
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        raw = row.get(key)
        if raw is None:
            continue
        try:
            out[int(raw)] = row
        except (TypeError, ValueError):
            continue
    return out
