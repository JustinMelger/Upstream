"""UI sections for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
import html
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block
from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.errors import safe_notify
from frontend.ui.nicegui.pages.courses.media import render_youtube_embed
from frontend.ui.nicegui.pages.courses.ui_glue import ActiveFilterChip


@dataclass
class CoursesFilterControls:
    """Filter control handles rendered in the left rail."""

    provider_filter: Any
    category_filter: Any
    level_filter: Any
    status_filter: Any
    refresh_btn: Any


@dataclass
class CoursesTopbarControls:
    """Topbar controls rendered for courses page."""

    search_input: Any
    scope_filter: Any
    sort_filter: Any
    meta: Any


def render_courses_topbar(*, initial_scope: str, on_share: Any) -> CoursesTopbarControls:
    """Render courses topbar and return controls."""
    with ui.row().classes("lp-topbar lp-sticky-controls"):
        search_input = (
            ui.input("Search courses").props("clearable debounce=300 dense").classes("lp-topbar-search").style("flex: 1")
        )
        with ui.row().classes("items-center gap-2 lp-topbar-group").style("margin-left: auto"):
            ui.label("View").classes("lp-topbar-group-label")
            scope_filter = (
                ui.radio(
                    {"all": "All", "tracked": "Tracked"},
                    value=initial_scope,
                )
                .props("inline dense")
                .classes("text-sm")
            )
        with ui.row().classes("items-center gap-2 lp-topbar-group"):
            ui.label("Sort").classes("lp-topbar-group-label")
            sort_filter = (
                ui.select(
                    {
                        "": "Recommended",
                        "top_rated": "Top rated",
                        "most_reviewed": "Most reviewed",
                        "newest": "Recently added",
                        "title_az": "Title A–Z",
                    },
                    value="",
                    label=None,
                )
                .props("dense")
                .style("min-width: 180px")
            )
        with ui.row().classes("items-center gap-2 lp-topbar-group"):
            ui.button("Share", on_click=on_share).props("dense")
        with ui.row().classes("items-center gap-2 lp-topbar-group"):
            meta = ui.label("").classes("lp-topbar-meta lp-topbar-count")
    return CoursesTopbarControls(
        search_input=search_input,
        scope_filter=scope_filter,
        sort_filter=sort_filter,
        meta=meta,
    )


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

    provider_filter = (
        ui.select({"": "Any provider"}, label="Provider", value="").props("dense").classes("w-full lp-filter-select")
    )
    category_filter = (
        ui.select({"": "Any category"}, label="Category", value="").props("dense").classes("w-full lp-filter-select")
    )
    status_filter = (
        ui.select(
            {"": "Any status", "not_tracked": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
            label="My status",
            value="",
        )
        .props("dense")
        .classes("w-full lp-filter-select")
    )
    with ui.expansion("More filters").props("dense"):
        with ui.column().classes("w-full"):
            level_filter = (
                ui.select({"": "Any level"}, label="Level (optional)", value="")
                .props("dense")
                .classes("w-full lp-filter-select")
            )

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
    status_select = (
        ui.select(
            options=options_map,
            value=current_status,
            label=None,
        )
        .props("dense outlined")
        .classes("lp-status-select")
    )
    status_select.style("min-width: 148px; max-width: 188px")
    status_select.props("use-input hide-selected fill-input")
    status_select.tooltip("Status")
    saved_hint = ui.label("").classes("lp-status-saved")

    async def _on_status_change(e: Any, _cid: int = int(course_id), _select=status_select) -> None:
        _select.disable()
        saved_hint.text = ""
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
                safe_notify(f"Invalid status: {value}", type="negative")
                return
            _select.value = value
            _select.update()
            await on_set_status(_cid, value)
            saved_hint.text = "Saved"
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
    has_video_preview: bool,
    is_preview_open: bool,
    preview_embed_url: str,
    on_toggle_preview: Any,
) -> None:
    """Render one course card including action menu and status control."""

    async def _on_primary_action() -> None:
        cid = int(course_row.get("id") or 0)
        current_status = str((tracked_row or {}).get("status") or "").strip()
        if current_status:
            actions.on_view()
            return
        await on_set_status(cid, "interested")

    with ui.card().classes(f"w-full lp-course-card lp-card--hover{card_vm.card_class_suffix}"):
        title = str(course_row.get("title") or "")
        with ui.element("div").classes("lp-card-topright"):
            if card_vm.is_new:
                ui.label("New").classes("lp-chip lp-chip--sky")
            elif card_vm.is_updated:
                ui.label("Updated").classes("lp-chip lp-chip--teal")
            with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                ui.menu_item("Review", actions.on_review)
                ui.menu_item("Recommend", actions.on_recommend)
                if has_video_preview:
                    ui.menu_item("Preview", on_toggle_preview)
                if has_url:
                    ui.menu_item("Copy link", actions.on_copy_link)
                if can_edit:
                    ui.menu_item("Edit", actions.on_edit)
                    ui.menu_item("Delete", actions.on_delete)

        thumbnail_url = str(getattr(card_vm, "thumbnail_url", "") or "").strip()
        with ui.row().classes("lp-course-card-main"):
            with ui.column().classes("lp-course-card-content"):
                ui.label(title).classes("text-lg font-semibold lp-card-title")
                shared_by = card_vm.shared_by
                with ui.row().classes("items-center gap-2 flex-wrap lp-social-strip"):
                    if shared_by:
                        ui.label(f"Shared by {shared_by}").classes("text-xs lp-card-subtitle").style("color: var(--lp-muted)")
                    if card_vm.rating_badge:
                        ui.label(card_vm.rating_badge).classes("lp-meta-chip")
                    if card_vm.recommendation_badge:
                        ui.label(card_vm.recommendation_badge).classes("lp-meta-chip")
                if str(course_row.get("description") or "").strip():
                    ui.label(str(course_row.get("description") or "")).classes("text-sm text-gray-600 lp-card-body")
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
                        ui.label(chip).classes("lp-meta-chip lp-meta-chip--quiet")
                    if len(chips) > max_chips:
                        ui.label(f"+{len(chips) - max_chips}").classes("lp-meta-chip lp-meta-chip--quiet")

                    ui.label(card_vm.tracking_label_text).classes(card_vm.tracking_chip_cls)

                with ui.row().classes("items-center gap-2 mt-2") as actions_row:
                    actions_row.classes("lp-card-actions")
                    primary_label = "Continue" if str((tracked_row or {}).get("status") or "").strip() else "Track"
                    ui.button(primary_label, on_click=_on_primary_action).props("dense")
                    ui.button("", icon="visibility", on_click=actions.on_view).props("outline dense").tooltip("Details")
                    if has_video_preview:
                        preview_label = "Hide preview" if bool(is_preview_open) else "Preview"
                        ui.button(preview_label, on_click=on_toggle_preview).props("outline dense")

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

            if thumbnail_url:
                thumbnail_fallback_url = str(getattr(card_vm, "thumbnail_fallback_url", "") or "").strip()
                safe_src = html.escape(thumbnail_url, quote=True)
                if thumbnail_fallback_url:
                    safe_fallback = html.escape(thumbnail_fallback_url, quote=True)
                    ui.html(
                        (
                            '<img class="lp-course-thumb lp-course-thumb--side" '
                            f'src="{safe_src}" '
                            f"onerror=\"this.onerror=null;this.src='{safe_fallback}';\" "
                            'alt="Course thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                        ),
                        sanitize=False,
                    )
                else:
                    ui.html(
                        (
                            '<img class="lp-course-thumb lp-course-thumb--side" '
                            f'src="{safe_src}" '
                            'alt="Course thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                        ),
                        sanitize=False,
                    )

        if bool(is_preview_open) and str(preview_embed_url or "").strip():
            with ui.element("div").classes("lp-video-wrap"):
                render_youtube_embed(str(preview_embed_url))
            source_url = str(course_row.get("url") or "").strip()
            if source_url:
                ui.link("Open source video", source_url).props("target=_blank").classes("text-xs")


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
        render_empty_block(
            title="No tracked courses yet.",
            description="Browse courses and set a status to start tracking.",
            primary_label="Browse all courses",
            on_primary=on_browse_all,
            secondary_label="Refresh",
            on_secondary=on_refresh,
        )
        return

    if (not has_any_courses) and (not any_filters):
        render_empty_block(
            title="No courses yet.",
            description="Share the first course to get started.",
            primary_label="Share a course",
            on_primary=on_share,
            secondary_label="Refresh",
            on_secondary=on_refresh,
        )
        return

    render_empty_block(
        title="No courses match your filters.",
        description="Try resetting filters to broaden results." if any_filters else "",
        primary_label="Reset all",
        on_primary=on_reset_all,
        secondary_label="Refresh",
        on_secondary=on_refresh,
    )


def render_load_more_control(
    *,
    shown_page_count: int,
    shown_total_count: int,
    on_load_more: Any,
) -> None:
    """Render the load-more control for paginated list rendering."""
    render_load_more_footer(
        shown_page_count=int(shown_page_count),
        shown_total_count=int(shown_total_count),
        on_load_more=on_load_more,
    )
