"""Small UI glue helpers for Paths page composition."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ActiveFilterChip(BaseModel):
    """UI chip metadata for active filter badges."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str


def collect_active_filter_chips(
    *,
    scope_value: str,
    search_value: str,
    status_value: str,
    sort_value: str,
    status_options: dict[str, str] | None = None,
    sort_options: dict[str, str] | None = None,
) -> list[ActiveFilterChip]:
    """Return active filter chip descriptors for current controls."""
    chips: list[ActiveFilterChip] = []
    if str(scope_value or "") == "selected":
        chips.append(ActiveFilterChip(key="scope", label="View: Selected"))
    needle = str(search_value or "").strip()
    if needle:
        chips.append(ActiveFilterChip(key="search", label=f"Search: {needle}"))
    status = str(status_value or "").strip()
    if status:
        label = str((status_options or {}).get(status) or status)
        chips.append(ActiveFilterChip(key="status", label=f"Status: {label}"))
    sort_key = str(sort_value or "").strip()
    if sort_key:
        sort_label = str((sort_options or {}).get(sort_key) or sort_key)
        chips.append(ActiveFilterChip(key="sort", label=f"Sort: {sort_label}"))
    return chips


def compute_paths_meta_text(*, path_count: int) -> str:
    """Build the top-bar list meta text."""
    return f"{int(path_count)} paths"


def compute_expanded_visible_count(*, current_visible: int, total_count: int, page_size: int) -> int:
    """Return next visible count for load-more pagination."""
    return min(int(total_count), int(current_visible) + int(page_size))
