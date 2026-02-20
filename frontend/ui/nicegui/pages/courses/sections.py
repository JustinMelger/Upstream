"""UI sections for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.pages.courses.ui_glue import ActiveFilterChip


@dataclass
class CoursesFilterControls:
    """Filter control handles rendered in the left rail."""

    provider_filter: Any
    category_filter: Any
    level_filter: Any
    status_filter: Any
    refresh_btn: Any


_ALLOWED_TRACKING_STATUSES = {"interested", "in_progress", "completed"}


def render_active_filter_chips(
    *,
    chips: list[ActiveFilterChip],
    on_clear_key: Any,
) -> None:
    """Render removable active-filter chips."""

    def _chip(label: str, on_clear: Any) -> None:
        with ui.row().classes("items-center"):
            with ui.element("div").classes("lp-filter-chip"):
                ui.label(label)
                ui.button("×", on_click=on_clear).props("dense flat")

    if not chips:
        return

    with ui.row().classes("items-center gap-2 w-full"):
        for chip in chips:
            def _clear(_key: str = chip.key) -> None:
                on_clear_key(_key)

            _chip(chip.label, _clear)


def render_filters_rail(
    *,
    on_refresh: Any,
    on_clear: Any,
    on_filters_changed: Any,
) -> CoursesFilterControls:
    """Render filter rail and return created control handles."""
    with ui.row().classes("items-center justify-between w-full"):
        ui.label("Filters").classes("text-md font-semibold")
        with ui.row().classes("items-center gap-2"):
            refresh_btn = ui.button("Refresh", on_click=on_refresh).props("outline dense")

    ui.label("Tip: use filters to narrow results.").classes("text-xs").style("color: var(--lp-muted)")

    provider_filter = ui.select({"": "Any provider"}, label="Provider", value="").props("dense").classes("w-full")
    category_filter = ui.select({"": "Any category"}, label="Category", value="").props("dense").classes("w-full")
    status_filter = (
        ui.select(
            {"": "Any status", "not_tracked": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
            label="My status",
            value="",
        )
        .props("dense")
        .classes("w-full")
    )
    with ui.expansion("More filters").props("dense"):
        with ui.column().classes("w-full"):
            level_filter = ui.select({"": "Any level"}, label="Level (optional)", value="").props("dense").classes("w-full")

    provider_filter.on("update:model-value", on_filters_changed)
    category_filter.on("update:model-value", on_filters_changed)
    level_filter.on("update:model-value", on_filters_changed)
    status_filter.on("update:model-value", on_filters_changed)
    ui.element("div").style("flex: 1")
    ui.button("Clear", on_click=on_clear).props("outline dense").classes("w-full")

    return CoursesFilterControls(
        provider_filter=provider_filter,
        category_filter=category_filter,
        level_filter=level_filter,
        status_filter=status_filter,
        refresh_btn=refresh_btn,
    )


def render_tracking_status_select(
    *,
    course_id: int,
    current_status: str,
    options_map: dict[str, str],
    is_tracked_course: Any,
    resolve_status_value: Any,
    on_set_status: Any,
    on_clear_status: Any,
) -> Any:
    """Render a tracking-status select and bind update behavior."""
    status_select = ui.select(
        options=options_map,
        value=current_status,
        label=None,
    ).props("dense")
    status_select.style("min-width: 170px")
    status_select.props("use-input hide-selected fill-input")
    status_select.tooltip("Status")

    async def _on_status_change(e: Any, _cid: int = int(course_id), _select=status_select) -> None:
        _select.disable()
        try:
            value = resolve_status_value(
                raw_event=e,
                options_map=options_map,
                fallback_value=str(_select.value or ""),
            )
            if not value:
                _select.value = ""
                _select.update()
                if bool(is_tracked_course(_cid)):
                    await on_clear_status(_cid)
                return
            if value not in _ALLOWED_TRACKING_STATUSES:
                ui.notify(f"Invalid status: {value}", type="negative")
                return
            _select.value = value
            _select.update()
            await on_set_status(_cid, value)
        finally:
            _select.enable()

    status_select.on("update:model-value", _on_status_change)
    return status_select


def render_course_card(
    *,
    course_row: dict[str, Any],
    tracked_row: dict[str, Any] | None,
    card_vm: Any,
    can_edit: bool,
    has_url: bool,
    actions: Any,
    is_tracked_course: Any,
    resolve_status_value: Any,
    on_set_status: Any,
    on_clear_status: Any,
) -> None:
    """Render one course card including action menu and status control."""
    with ui.card().classes(f"w-full lp-course-card lp-card--hover{card_vm.card_class_suffix}"):
        with ui.row().classes("items-start justify-between w-full"):
            with ui.column().classes("gap-1"):
                title = str(course_row.get("title") or "")
                with ui.element("div").classes("lp-card-topright"):
                    if card_vm.is_new:
                        ui.label("New").classes("lp-chip lp-chip--sky")
                    elif card_vm.is_updated:
                        ui.label("Updated").classes("lp-chip lp-chip--teal")
                    if card_vm.rating_badge:
                        ui.label(card_vm.rating_badge).classes("lp-meta-chip")
                    if card_vm.recommendation_badge:
                        ui.label(card_vm.recommendation_badge).classes("lp-meta-chip")
                    with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                        ui.menu_item("Review", actions.on_review)
                        ui.menu_item("Recommend", actions.on_recommend)
                        if has_url:
                            ui.menu_item("Copy link", actions.on_copy_link)
                        if can_edit:
                            ui.menu_item("Edit", actions.on_edit)
                            ui.menu_item("Delete", actions.on_delete)

                ui.label(title).classes("text-lg font-semibold")
                shared_by = card_vm.shared_by
                if shared_by:
                    ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                if str(course_row.get("description") or "").strip():
                    ui.label(str(course_row.get("description") or "")).classes("text-sm text-gray-600")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    chips: list[str] = []
                    if str(course_row.get("provider") or "").strip():
                        chips.append(str(course_row.get("provider") or "").strip())
                    if str(course_row.get("category") or "").strip():
                        chips.append(str(course_row.get("category") or "").strip())
                    if str(course_row.get("language") or "").strip():
                        chips.append(str(course_row.get("language") or "").strip())

                    max_chips = 2
                    for chip in chips[:max_chips]:
                        ui.label(chip).classes("lp-meta-chip")
                    if len(chips) > max_chips:
                        ui.label(f"+{len(chips) - max_chips}").classes("lp-meta-chip")

                    ui.label(card_vm.tracking_label_text).classes(card_vm.tracking_chip_cls)

            with ui.column().classes("items-end gap-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.button("", icon="visibility", on_click=actions.on_view).props("outline dense").tooltip("View")

                    current_status = str((tracked_row or {}).get("status") or "")
                    options_map = {
                        "": "Not tracked",
                        **{k: v for k, v in TRACKING_STATUS_OPTIONS},
                    }
                    render_tracking_status_select(
                        course_id=int(course_row.get("id") or 0),
                        current_status=current_status,
                        options_map=options_map,
                        is_tracked_course=is_tracked_course,
                        resolve_status_value=resolve_status_value,
                        on_set_status=on_set_status,
                        on_clear_status=on_clear_status,
                    )


def render_courses_empty_state(
    *,
    scope_value: str,
    any_filters: bool,
    has_any_courses: bool,
    on_browse_all: Any,
    on_share: Any,
    on_reset_all: Any,
    on_refresh: Any,
) -> None:
    """Render empty-state variants for courses list."""
    if scope_value == "tracked" and not any_filters:
        ui.label("No tracked courses yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Browse courses and set a status to start tracking.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Browse all courses", on_click=on_browse_all).props("outline")
            ui.button("Refresh", on_click=on_refresh).props("outline")
        return

    if (not has_any_courses) and (not any_filters):
        ui.label("No courses yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Share the first course to get started.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Share a course", on_click=on_share).props("outline")
            ui.button("Refresh", on_click=on_refresh).props("outline")
        return

    ui.label("No courses match your filters.").classes("text-sm").style("color: var(--lp-muted)")
    if any_filters:
        ui.label("Try resetting filters to broaden results.").classes("text-xs").style("color: var(--lp-muted)")
    with ui.row().classes("items-center gap-2"):
        ui.button("Reset all", on_click=on_reset_all).props("outline")
        ui.button("Refresh", on_click=on_refresh).props("outline")


def render_load_more_control(
    *,
    shown_page_count: int,
    shown_total_count: int,
    on_load_more: Any,
) -> None:
    """Render the load-more control for paginated list rendering."""
    if shown_total_count <= shown_page_count:
        return
    with ui.row().classes("items-center justify-center mt-2"):
        ui.button(
            f"Load more ({shown_page_count}/{shown_total_count})",
            on_click=on_load_more,
        ).props("outline")
