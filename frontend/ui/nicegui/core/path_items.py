"""Pure helpers for typed learning items inside paths."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.learning_items import learning_item_type_label, normalize_learning_item_type


def encode_path_item_ref(*, item_type: str, item_id: int) -> str:
    """Encode a typed learning-item reference for select controls."""
    return f"{normalize_learning_item_type(item_type)}:{int(item_id)}"


def decode_path_item_ref(raw: Any) -> tuple[str, int] | None:
    """Decode a typed learning-item reference from select control values."""
    try:
        item_type_raw, item_id_raw = str(raw or "").split(":", 1)
        item_type = normalize_learning_item_type(item_type_raw)
        item_id = int(item_id_raw)
    except (TypeError, ValueError):
        return None
    if item_id <= 0:
        return None
    return item_type, item_id


def build_path_item_payloads(values: list[Any] | None) -> list[dict[str, Any]]:
    """Convert ordered select values into typed path-item payload rows."""
    items: list[dict[str, Any]] = []
    for idx, raw in enumerate(list(values or [])):
        decoded = decode_path_item_ref(raw)
        if decoded is None:
            continue
        item_type, item_id = decoded
        items.append({"type": item_type, "id": item_id, "position": idx})
    return items


def count_course_items(*, detail: dict[str, Any] | None) -> int:
    """Count course-backed items in a path detail payload."""
    if not isinstance(detail, dict):
        return 0
    items = [row for row in list(detail.get("items") or []) if isinstance(row, dict)]
    if items:
        return sum(1 for row in items if normalize_learning_item_type(str(row.get("type") or ""), default="course") == "course")
    return len([row for row in list(detail.get("courses") or []) if isinstance(row, dict)])


def path_course_ids(*, detail: dict[str, Any] | None) -> list[int]:
    """Extract ordered course ids from a path detail payload."""
    if not isinstance(detail, dict):
        return []
    items = [row for row in list(detail.get("items") or []) if isinstance(row, dict)]
    out: list[int] = []
    if items:
        for row in items:
            if normalize_learning_item_type(str(row.get("type") or ""), default="course") != "course":
                continue
            try:
                cid = int(row.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid > 0:
                out.append(cid)
        return out
    for row in list(detail.get("courses") or []):
        if not isinstance(row, dict):
            continue
        try:
            cid = int(row.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if cid > 0:
            out.append(cid)
    return out


def learning_item_option_label(*, item_type: str, row: dict[str, Any]) -> str:
    """Build a readable select-option label for one learning item."""
    title = str(row.get("title") or "").strip() or f"{learning_item_type_label(item_type)} #{int(row.get('id') or 0)}"
    provider = str(row.get("provider") or "").strip()
    category = str(row.get("category") or "").strip()
    bits = [learning_item_type_label(item_type)]
    if provider:
        bits.append(provider)
    if category:
        bits.append(category)
    return f"{title} ({' · '.join(bits)})"
