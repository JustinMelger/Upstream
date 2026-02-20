"""Pure UI glue helpers for the Learning page."""

from __future__ import annotations

from typing import Any


def compute_next_visibility(
    *,
    reset_visibility: bool,
    page_size: int,
    tracked_visible: int,
    selected_visible: int,
) -> tuple[int, int]:
    """Return next tracked/selected visible counts after a load operation."""
    if reset_visibility:
        return int(page_size), int(page_size)
    return int(tracked_visible), int(selected_visible)


def compute_meta_text(*, data: dict[str, Any], view: str, feature_articles: bool) -> str:
    """Build top-bar meta text for either learning or shared view."""
    if str(view or "") == "shared":
        text = f"{len(list(data.get('shared_courses') or []))} courses · {len(list(data.get('shared_paths') or []))} paths"
        if feature_articles:
            text += f" · {len(list(data.get('shared_articles') or []))} articles"
        return text
    return (
        f"{len(list(data.get('tracked_courses') or []))} tracked courses · "
        f"{len(list(data.get('selected_paths') or []))} selected paths"
    )


def compute_expanded_visible_count(*, current_visible: int, total_count: int, page_size: int) -> int:
    """Return next visible count for load-more behavior."""
    return min(int(total_count), int(current_visible) + int(page_size))


def resolve_tracking_status_value(
    *,
    raw_event: Any,
    options_map: dict[str, str],
    fallback_value: str,
) -> str:
    """Normalize NiceGUI/Quasar select payloads to backend status keys."""
    raw = raw_event
    if not isinstance(raw_event, (str, int, float, bool, dict)) and raw_event is not None:
        raw = getattr(raw_event, "value", None)
        if raw is None:
            raw = getattr(raw_event, "args", None)

    if isinstance(raw, dict):
        selected = raw.get("value")
        if selected in options_map:
            return str(selected or "")
        label = str(raw.get("label") or "").strip().lower()
        if label:
            for key, opt_label in options_map.items():
                if label == str(opt_label).strip().lower():
                    return str(key)
        return ""
    return str(raw or fallback_value or "")
