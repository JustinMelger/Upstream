"""UI sections for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
import html
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_frame import (
    render_card_actions_row,
    render_card_content_column,
    render_card_main_row,
    render_card_topright,
)
from frontend.ui.nicegui.components.feedback import render_empty_block
from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.components.status_chips import tracking_label, TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.core.errors import safe_notify
from frontend.ui.nicegui.pages.courses.media import render_youtube_embed
from frontend.ui.nicegui.pages.courses.ui_glue import (
    ActiveFilterChip,
    normalize_course_tracking_status,
    primary_course_cta_label_for_status,
)


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
    filters_btn: Any
    meta: Any


def render_courses_topbar(*, initial_scope: str, on_share: Any, on_open_filters: Any) -> CoursesTopbarControls:
    """Render courses topbar and return controls."""
    with ui.row().classes("lp-topbar lp-sticky-controls lp-courses-toolbar"):
        search_input = (
            ui.input("Search courses")
            .props("clearable debounce=300 dense")
            .classes("lp-topbar-search lp-courses-search")
            .style("flex: 1")
        )
        with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
            ui.label("View").classes("lp-topbar-group-label")
            scope_filter = (
                ui.radio(
                    {"all": "All", "tracked": "Tracked"},
                    value=initial_scope,
                )
                .props("inline dense")
                .classes("text-sm lp-topbar-secondary-control")
            )
        with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
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
                .classes("lp-topbar-secondary-control")
            )
        with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
            filters_btn = ui.button("Filters", on_click=on_open_filters).props("dense outline").classes("lp-topbar-share")
            topbar_menu = apply_icon_button_a11y(
                ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"),
                label="Open course toolbar actions",
                tooltip="More actions",
            )
            with topbar_menu:
                ui.menu_item("Share course", on_share)
        with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
            meta = ui.label("").classes("lp-topbar-meta lp-topbar-count lp-topbar-meta--quiet")
    return CoursesTopbarControls(
        search_input=search_input,
        scope_filter=scope_filter,
        sort_filter=sort_filter,
        filters_btn=filters_btn,
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
    with ui.row().classes("items-center justify-between w-full lp-filters-head"):
        ui.label("Filters").classes("text-md font-semibold")
        with ui.row().classes("items-center gap-2"):
            refresh_btn = ui.button("Refresh", on_click=on_refresh).props("outline dense")

    ui.label("Tip: use filters to narrow results.").classes("text-xs lp-filters-tip").style("color: var(--lp-muted)")

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
        current_status = normalize_course_tracking_status((tracked_row or {}).get("status"))
        if current_status == "completed":
            await actions.on_review()
            return
        if current_status == "in_progress":
            await actions.on_view()
            return
        await on_set_status(cid, "in_progress")
        await actions.on_view()

    with ui.card().classes(f"w-full lp-course-card lp-course-card--surface lp-card--hover{card_vm.card_class_suffix}"):
        title = str(course_row.get("title") or "")
        with render_card_topright():
            if card_vm.is_new:
                ui.label("New").classes("lp-chip lp-chip--sky")
            elif card_vm.is_updated:
                ui.label("Updated").classes("lp-chip lp-chip--teal")
            card_menu = apply_icon_button_a11y(
                ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"),
                label="Open course actions",
                tooltip="Course actions",
            )
            with card_menu:
                ui.menu_item("Open details", actions.on_view)
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
        with render_card_main_row(classes="lp-course-card-main"):
            with render_card_content_column(classes="lp-course-card-content lp-course-card-stack"):
                ui.label(title).classes("text-lg font-semibold lp-card-title")
                shared_by = card_vm.shared_by
                with ui.row().classes("items-center gap-2 flex-wrap lp-social-strip"):
                    if shared_by:
                        ui.label(f"Shared by {shared_by}").classes("text-xs lp-card-subtitle").style("color: var(--lp-muted)")
                    if card_vm.rating_badge:
                        ui.label(card_vm.rating_badge).classes("lp-meta-chip lp-meta-chip--rating")
                    if card_vm.recommendation_badge:
                        ui.label(card_vm.recommendation_badge).classes("lp-meta-chip")
                context_bits: list[str] = []
                rating_text = str(card_vm.rating_badge or "").strip()
                if rating_text:
                    context_bits.append(rating_text)
                category_text = str(course_row.get("category") or "").strip()
                if category_text:
                    context_bits.append(category_text)
                duration_raw = course_row.get("duration_hours")
                try:
                    duration_value = float(duration_raw) if duration_raw is not None else 0.0
                except (TypeError, ValueError):
                    duration_value = 0.0
                if duration_value > 0:
                    duration_label = f"{int(duration_value)}h" if duration_value.is_integer() else f"{duration_value:.1f}h"
                    context_bits.append(duration_label)
                level_text = str(course_row.get("level") or "").strip()
                if level_text:
                    context_bits.append(level_text)
                if context_bits:
                    ui.label(" • ".join(context_bits)).classes("text-xs lp-card-subtitle lp-course-context-line")
                if str(course_row.get("description") or "").strip():
                    ui.label(str(course_row.get("description") or "")).classes(
                        "text-sm text-gray-600 lp-card-body lp-course-summary"
                    )
                current_status = normalize_course_tracking_status((tracked_row or {}).get("status"))
                ui.label(f"Status: {tracking_label(current_status)}").classes("lp-course-status-line")
                with ui.row().classes("items-center gap-2 flex-wrap lp-card-taxonomy"):
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

                    if current_status != "interested":
                        ui.label(card_vm.tracking_label_text).classes(f"{card_vm.tracking_chip_cls} lp-course-status-chip")

                def _render_actions() -> None:
                    current_status = normalize_course_tracking_status((tracked_row or {}).get("status"))
                    primary_label = primary_course_cta_label_for_status(current_status)
                    ui.button(primary_label, on_click=_on_primary_action).props("dense")

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

                render_card_actions_row(render_actions=_render_actions)

            if thumbnail_url:
                with ui.element("div").classes("lp-course-media-slot"):
                    thumbnail_fallback_url = str(getattr(card_vm, "thumbnail_fallback_url", "") or "").strip()
                    safe_src = html.escape(thumbnail_url, quote=True)
                    thumb_class = "lp-course-thumb lp-course-thumb--side"
                    if not bool(has_video_preview):
                        thumb_class += " lp-course-thumb--contain"
                    if thumbnail_fallback_url:
                        safe_fallback = html.escape(thumbnail_fallback_url, quote=True)
                        ui.html(
                            (
                                f'<img class="{thumb_class}" '
                                f'src="{safe_src}" '
                                f"onerror=\"this.onerror=null;this.src='{safe_fallback}';\" "
                                'alt="Course thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                            ),
                            sanitize=False,
                        )
                    else:
                        ui.html(
                            (
                                f'<img class="{thumb_class}" '
                                f'src="{safe_src}" '
                                'alt="Course thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                            ),
                            sanitize=False,
                        )

        if bool(is_preview_open) and str(preview_embed_url or "").strip():
            with ui.element("div").classes("lp-video-wrap"):
                ui.html(render_youtube_embed(str(preview_embed_url)), sanitize=False)
            source_url = str(course_row.get("url") or "").strip()
            if source_url:
                ui.link("Open source video", source_url).props("target=_blank").classes("text-xs")


def render_courses_catalog(
    *,
    shown_page: list[dict[str, Any]],
    render_course_item: Any,
    featured_title: str = "Featured course",
    featured_subtitle: str = "Top result from your current filters",
    collection_title: str = "Browse collection",
    show_featured: bool = True,
    max_groups: int | None = None,
    min_group_size: int = 1,
    overflow_group_title: str = "More for you",
    prioritize_larger_groups: bool = False,
) -> None:
    """Render featured + streaming-rail catalog sections for the current page slice."""
    featured_course = shown_page[0] if (shown_page and bool(show_featured)) else None
    remaining_courses = shown_page[1:] if (len(shown_page) > 1 and bool(show_featured)) else list(shown_page or [])

    if featured_course:
        with ui.column().classes("w-full gap-2 lp-courses-section"):
            ui.label(str(featured_title)).classes("lp-courses-section-title")
            ui.label(str(featured_subtitle)).classes("lp-courses-section-subtitle")
            with ui.element("div").classes("lp-courses-grid"):
                render_course_item(
                    featured_course,
                    item_classes="lp-courses-grid-item lp-courses-grid-item--featured",
                )

    if not remaining_courses:
        return

    grouped_by_category: dict[str, list[dict[str, Any]]] = {}
    for row in remaining_courses:
        category_key = str(row.get("category") or "").strip() or "General"
        grouped_by_category.setdefault(category_key, []).append(row)

    if int(min_group_size) > 1:
        compacted: dict[str, list[dict[str, Any]]] = {}
        overflow_rows: list[dict[str, Any]] = []
        for category_name, rows in grouped_by_category.items():
            if len(rows) < int(min_group_size):
                overflow_rows.extend(rows)
            else:
                compacted[category_name] = rows
        if overflow_rows:
            compacted.setdefault(str(overflow_group_title or "More for you"), []).extend(overflow_rows)
        grouped_by_category = compacted

    groups: list[tuple[str, list[dict[str, Any]]]] = list(grouped_by_category.items())
    if bool(prioritize_larger_groups):
        groups = sorted(groups, key=lambda item: len(item[1]), reverse=True)

    if max_groups is not None and int(max_groups) > 0 and len(groups) > int(max_groups):
        keep_count = max(1, int(max_groups) - 1)
        visible = groups[:keep_count]
        hidden = groups[keep_count:]
        hidden_rows: list[dict[str, Any]] = []
        for _, rows in hidden:
            hidden_rows.extend(rows)
        if hidden_rows:
            visible.append((str(overflow_group_title or "More for you"), hidden_rows))
        groups = visible

    with ui.column().classes("w-full gap-3 lp-courses-section"):
        ui.label(str(collection_title)).classes("lp-courses-collection-title")
        for row_idx, (category_name, rows) in enumerate(groups):
            rail_id = f"lp-courses-rail-{row_idx}"
            left_btn_id = f"{rail_id}-left"
            right_btn_id = f"{rail_id}-right"
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("items-center justify-between w-full lp-courses-row-head"):
                    ui.label(category_name).classes("lp-courses-row-title")
                    with ui.row().classes("items-center gap-2 lp-courses-rail-controls"):
                        ui.button(
                            icon="chevron_left",
                            on_click=lambda _rid=rail_id: ui.run_javascript(
                                (
                                    "(() => {"
                                    f"const el = document.getElementById('{_rid}');"
                                    "if (el) { el.scrollBy({ left: -460, behavior: 'smooth' }); }"
                                    "})();"
                                )
                            ),
                        ).props(f'dense flat round id="{left_btn_id}"').classes("lp-rail-nav-btn")
                        ui.button(
                            icon="chevron_right",
                            on_click=lambda _rid=rail_id: ui.run_javascript(
                                (
                                    "(() => {"
                                    f"const el = document.getElementById('{_rid}');"
                                    "if (el) { el.scrollBy({ left: 460, behavior: 'smooth' }); }"
                                    "})();"
                                )
                            ),
                        ).props(f'dense flat round id="{right_btn_id}"').classes("lp-rail-nav-btn")
                with ui.element("div").classes("lp-courses-rail").props(f'id="{rail_id}"'):
                    for idx, c in enumerate(rows):
                        item_classes = "lp-courses-rail-item"
                        if idx == 0:
                            item_classes += " lp-courses-rail-item--hero"
                        render_course_item(c, item_classes=item_classes)
            _bind_rail_arrow_visibility(
                rail_id=rail_id,
                left_btn_id=left_btn_id,
                right_btn_id=right_btn_id,
            )


def _bind_rail_arrow_visibility(*, rail_id: str, left_btn_id: str, right_btn_id: str) -> None:
    """Bind arrow visibility and edge behavior for one horizontal course rail."""
    ui.run_javascript(
        (
            "(() => {"
            f"const rail = document.getElementById('{rail_id}');"
            f"const left = document.getElementById('{left_btn_id}');"
            f"const right = document.getElementById('{right_btn_id}');"
            "if (!rail || !left || !right) return;"
            "const update = () => {"
            "  const maxScroll = Math.max(0, rail.scrollWidth - rail.clientWidth);"
            "  const x = Math.max(0, rail.scrollLeft);"
            "  if (maxScroll <= 2) { left.style.display = 'none'; right.style.display = 'none'; return; }"
            "  left.style.display = x <= 2 ? 'none' : '';"
            "  right.style.display = x >= (maxScroll - 2) ? 'none' : '';"
            "};"
            "if (!rail.dataset.lpBound) {"
            "  rail.addEventListener('scroll', update, { passive: true });"
            "  window.addEventListener('resize', update);"
            "  rail.dataset.lpBound = '1';"
            "}"
            "setTimeout(update, 0);"
            "})();"
        )
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
        render_empty_block(
            title="No active learning queue yet.",
            description="Browse courses and mark one as Interested or In progress to start momentum.",
            primary_label="Browse all courses",
            on_primary=on_browse_all,
        )
        return

    if (not has_any_courses) and (not any_filters):
        render_empty_block(
            title="No course library yet.",
            description="Share the first course and seed the learning catalog.",
            primary_label="Share a course",
            on_primary=on_share,
        )
        return

    render_empty_block(
        title="No learning matches this filter set.",
        description="Reset filters to widen the course pipeline." if any_filters else "",
        primary_label="Reset all",
        on_primary=on_reset_all,
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
