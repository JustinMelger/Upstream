"""Pure UI glue helpers for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActiveFilterChip:
    """Descriptor for a removable active-filter chip."""

    key: str
    label: str


@dataclass(frozen=True)
class CoursesFilterResetState:
    """Default filter state for a full reset action."""

    scope: str
    search: str
    provider: str
    category: str
    level: str
    status: str
    sort: str


def default_courses_filter_reset_state() -> CoursesFilterResetState:
    """Return default values used by the 'Reset all' action."""
    return CoursesFilterResetState(
        scope="all",
        search="",
        provider="",
        category="",
        level="",
        status="",
        sort="",
    )


def compute_courses_meta_text(*, course_count: int) -> str:
    """Build the top-bar list meta text."""
    return f"{int(course_count)} courses"


def compute_expanded_visible_count(*, current_visible: int, total_count: int, page_size: int) -> int:
    """Return next visible card count for load-more behavior."""
    return min(int(total_count), int(current_visible) + int(page_size))


def build_active_filter_chips(
    *,
    scope_value: str,
    search_value: str,
    provider_value: str,
    category_value: str,
    level_value: str,
    status_value: str,
    status_options: dict[str, str],
) -> list[ActiveFilterChip]:
    """Build active-filter chip descriptors for currently selected filters."""
    chips: list[ActiveFilterChip] = []
    if str(scope_value or "") == "tracked":
        chips.append(ActiveFilterChip(key="scope", label="View: Tracked"))

    search = str(search_value or "").strip()
    if search:
        chips.append(ActiveFilterChip(key="search", label=f"Search: {search}"))

    provider = str(provider_value or "").strip()
    if provider:
        chips.append(ActiveFilterChip(key="provider", label=f"Provider: {provider}"))

    category = str(category_value or "").strip()
    if category:
        chips.append(ActiveFilterChip(key="category", label=f"Category: {category}"))

    level = str(level_value or "").strip()
    if level:
        chips.append(ActiveFilterChip(key="level", label=f"Level: {level}"))

    status = str(status_value or "").strip()
    if status:
        label = str(status_options.get(status) or status)
        chips.append(ActiveFilterChip(key="status", label=f"Status: {label}"))
    return chips


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
