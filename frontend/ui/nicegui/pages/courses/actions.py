"""Card-level actions for the Courses page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import json
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.errors import safe_notify


@dataclass(slots=True)
class CourseCardActions:
    """Callback bundle for a single course card."""

    on_view: Callable[[], Awaitable[None]]
    on_review: Callable[[], Awaitable[None]]
    on_recommend: Callable[[], Awaitable[None]]
    on_copy_link: Callable[[], None]
    on_edit: Callable[[], None]
    on_delete: Callable[[], Awaitable[None]]


@dataclass(slots=True)
class CoursesFilterControls:
    """UI controls used by filter-clear/reset handlers."""

    scope_filter: Any
    search_input: Any
    provider_filter: Any
    category_filter: Any
    level_filter: Any
    status_filter: Any
    sort_filter: Any


def recompute_course_facet_controls(
    *,
    controls: CoursesFilterControls,
    courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    normalized_filters: Any,
    compute_facet_counts: Callable[..., tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]],
    build_count_options: Callable[..., dict[str, str]],
    build_status_options: Callable[..., dict[str, str]],
) -> None:
    """Recompute facet options and apply values/updates to controls."""
    provider_counts, category_counts, level_counts, status_counts = compute_facet_counts(
        courses=courses,
        tracking_by_course_id=tracking_by_course_id,
        scope_value=str(normalized_filters.scope),
        needle=str(normalized_filters.search),
        provider_value=str(normalized_filters.provider),
        category_value=str(normalized_filters.category),
        level_value=str(normalized_filters.level),
        status_value=str(normalized_filters.status),
    )

    # Preserve selected values even when they drop to 0-count after other filters.
    selected_provider = str(controls.provider_filter.value or "").strip()
    if selected_provider and selected_provider not in provider_counts:
        provider_counts[selected_provider] = 0
    selected_category = str(controls.category_filter.value or "").strip()
    if selected_category and selected_category not in category_counts:
        category_counts[selected_category] = 0
    selected_level = str(controls.level_filter.value or "").strip()
    if selected_level and selected_level not in level_counts:
        level_counts[selected_level] = 0

    controls.provider_filter.options = build_count_options(any_label="Any provider", counts=provider_counts)
    controls.category_filter.options = build_count_options(any_label="Any category", counts=category_counts)
    controls.level_filter.options = build_count_options(any_label="Any level", counts=level_counts)
    controls.status_filter.options = build_status_options(status_counts=status_counts)

    if controls.provider_filter.value and controls.provider_filter.value not in controls.provider_filter.options:
        controls.provider_filter.value = ""
    if controls.category_filter.value and controls.category_filter.value not in controls.category_filter.options:
        controls.category_filter.value = ""
    if controls.level_filter.value and controls.level_filter.value not in controls.level_filter.options:
        controls.level_filter.value = ""
    if controls.status_filter.value and controls.status_filter.value not in controls.status_filter.options:
        controls.status_filter.value = ""

    controls.provider_filter.update()
    controls.category_filter.update()
    controls.level_filter.update()
    controls.status_filter.update()


def copy_course_link(*, url: str) -> None:
    """Copy a course URL to clipboard."""
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(str(url or ''))});")
    safe_notify("Link copied", type="positive")


def build_course_card_actions(
    *,
    course_id: int,
    course_url: str,
    course_row: dict,
    on_open_details: Callable[[int, bool], Awaitable[None]],
    on_open_recommend: Callable[[int], Awaitable[None]],
    on_open_edit: Callable[[dict], None],
    on_confirm_delete: Callable[[int], Awaitable[None]],
) -> CourseCardActions:
    """Build per-card callbacks to keep page view logic minimal."""

    async def _view() -> None:
        await on_open_details(int(course_id), False)

    async def _review() -> None:
        await on_open_details(int(course_id), True)

    async def _recommend() -> None:
        await on_open_recommend(int(course_id))

    def _copy_link() -> None:
        copy_course_link(url=course_url)

    def _edit() -> None:
        on_open_edit(course_row)

    async def _delete() -> None:
        await on_confirm_delete(int(course_id))

    return CourseCardActions(
        on_view=_view,
        on_review=_review,
        on_recommend=_recommend,
        on_copy_link=_copy_link,
        on_edit=_edit,
        on_delete=_delete,
    )


def clear_course_filter_by_key(*, key: str, controls: CoursesFilterControls) -> bool:
    """Clear a single course filter key and update its control."""
    k = str(key or "")
    if k == "scope":
        controls.scope_filter.value = "all"
        controls.scope_filter.update()
        return True
    if k == "search":
        controls.search_input.value = ""
        controls.search_input.update()
        return True
    if k == "provider":
        controls.provider_filter.value = ""
        controls.provider_filter.update()
        return True
    if k == "category":
        controls.category_filter.value = ""
        controls.category_filter.update()
        return True
    if k == "level":
        controls.level_filter.value = ""
        controls.level_filter.update()
        return True
    if k == "status":
        controls.status_filter.value = ""
        controls.status_filter.update()
        return True
    return False


def reset_course_filter_controls(*, controls: CoursesFilterControls, reset_state: Any) -> None:
    """Apply default reset state to all filter controls and update them."""
    controls.scope_filter.value = str(reset_state.scope)
    controls.search_input.value = str(reset_state.search)
    controls.provider_filter.value = str(reset_state.provider)
    controls.category_filter.value = str(reset_state.category)
    controls.level_filter.value = str(reset_state.level)
    controls.status_filter.value = str(reset_state.status)
    controls.sort_filter.value = str(reset_state.sort)
    controls.scope_filter.update()
    controls.search_input.update()
    controls.provider_filter.update()
    controls.category_filter.update()
    controls.level_filter.update()
    controls.status_filter.update()
    controls.sort_filter.update()
