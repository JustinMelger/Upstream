"""UI sections for the Learning page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.errors import FrontendError, safe_notify
from frontend.ui.nicegui.core.learning_items import (
    learning_item_primary_action_label,
    learning_item_review_action_label,
    learning_item_type_label,
)


_ALLOWED_TRACKING_STATUSES = {"interested", "in_progress", "completed"}


@dataclass(slots=True)
class LearningTabContext:
    """Bundled dependencies for rendering the learning tab."""

    learning_vm: Any
    state: Any
    next_course: dict[str, Any] | None
    first_course_review_action: Any
    first_path_review_action: Any
    review_summary_label: Any
    tracking_label_fn: Any
    progress_for_path_detail: Any
    nav_actions: Any
    on_set_tracking_status: Any
    on_clear_tracking_status: Any
    on_browse_courses: Any
    on_browse_paths: Any
    on_open_selected_paths: Any
    on_open_full_stats: Any
    recently_shared_in_teams: list[dict[str, Any]]
    on_open_recently_shared_item: Any
    on_load_more_selected: Any


def _tracking_status_counts(*, tracking_by_course_id: dict[int, dict[str, Any]]) -> tuple[int, int, int]:
    """Return (interested, in_progress, completed) tracking totals."""
    interested = 0
    in_progress = 0
    completed = 0
    for row in list((tracking_by_course_id or {}).values()):
        status = str((row or {}).get("status") or "").strip()
        if status == "interested":
            interested += 1
        elif status == "in_progress":
            in_progress += 1
        elif status == "completed":
            completed += 1
    return interested, in_progress, completed


def render_tracking_status_select(
    *,
    course_id: int,
    current_status: str,
    options_map: dict[str, str],
    resolve_status_value: Any,
    on_set_status: Any,
    on_clear_status: Any,
) -> Any:
    """Render tracking status select and wire update handling."""
    status_select = ui.select(
        options=options_map,
        value=current_status,
        label=None,
    ).props("dense dropdown-icon=tune")
    if hasattr(status_select, "classes"):
        status_select.classes("lp-home-track-status-select")
    status_select.props("use-input hide-selected fill-input")
    status_select.tooltip("Status")

    async def _on_status_change(e: Any, _cid: int = int(course_id), _select: Any = status_select) -> None:
        _select.disable()
        previous_value = str(_select.value or "")
        try:
            value = resolve_status_value(
                raw_event=e,
                options_map=options_map,
                fallback_value=str(_select.value or ""),
            )
            if value and value not in _ALLOWED_TRACKING_STATUSES:
                safe_notify(f"Invalid status: {value}", type="negative")
                _select.value = previous_value
                _select.update()
                return
            _select.value = value
            _select.update()
            if not value:
                try:
                    await on_clear_status(_cid)
                except (ApiError, FrontendError, RuntimeError):
                    _select.value = previous_value
                    _select.update()
                    raise
                return
            try:
                await on_set_status(_cid, value)
            except (ApiError, FrontendError, RuntimeError):
                _select.value = previous_value
                _select.update()
                raise
        finally:
            _select.enable()

    status_select.on("update:model-value", _on_status_change)
    return status_select


def _tracked_progress_percent(*, status: str) -> int:
    """Return a display progress percentage from tracking status."""
    normalized = str(status or "").strip().lower()
    if normalized == "completed":
        return 100
    if normalized == "in_progress":
        return 45
    if normalized == "interested":
        return 0
    return 0


def _tracked_status_tone(*, status: str) -> str:
    """Return semantic tone class for tracked status marker."""
    normalized = str(status or "").strip().lower()
    if normalized == "completed":
        return "lp-home-status--done"
    if normalized == "in_progress":
        return "lp-home-status--active"
    return "lp-home-status--idle"


def _format_duration_hours(duration_raw: Any) -> str:
    """Return compact duration text for tracked-course metadata."""
    if duration_raw is None:
        return ""
    try:
        duration_value = float(duration_raw)
    except (TypeError, ValueError):
        return ""
    if duration_value <= 0:
        return ""
    if duration_value.is_integer():
        return f"{int(duration_value)}h"
    return f"{duration_value:.1f}h"


def _render_tracked_course_card(
    *,
    index: int,
    course: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
    course_review_summary_by_id: dict[int, dict[str, Any]],
    tracking_label_fn: Any,
    on_view_course: Any,
    on_review_course: Any,
    on_set_status: Any,
    on_clear_status: Any,
) -> None:
    """Render one tracked-course card in the Home dashboard."""
    course_id = int(course.get("id") or 0)
    tracking_row = tracking_by_course_id.get(course_id) or {}
    status = str(tracking_row.get("status") or "")
    progress_pct = _tracked_progress_percent(status=status)
    tone_class = _tracked_status_tone(status=status)
    teammates_active = int((course_review_summary_by_id.get(course_id) or {}).get("review_count") or 0)
    source_url = str(course.get("url") or "").strip()
    card_tier_class = "lp-track-card--primary" if index == 0 else "lp-track-card--secondary"
    card_size_class = "lp-track-card--major" if index == 0 else "lp-track-card--minor"

    with ui.element("div").classes(f"lp-track-card {card_tier_class} {card_size_class} w-full"):
        with ui.row().classes("w-full items-start justify-between gap-3 lp-track-head-row"):
            with ui.row().classes("items-start gap-2 lp-track-identity"):
                ui.icon("school").classes("lp-track-avatar")
                with ui.column().classes("gap-0 lp-track-title-block"):
                    ui.label(str(course.get("title") or "")).classes("text-sm font-semibold lp-track-title")
                    bits = [
                        bit
                        for bit in [
                            str(course.get("provider") or "").strip(),
                            _format_duration_hours(course.get("duration_hours")),
                            str(course.get("level") or "").strip(),
                        ]
                        if bit
                    ]
                    if bits:
                        ui.label(" · ".join(bits)).classes("text-xs lp-home-track-meta").style("color: var(--lp-muted)")

            with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group"):
                if source_url:
                    ui.button("Continue course", on_click=lambda u=source_url: ui.navigate.to(u, new_tab=True)).props(
                        "dense outline"
                    ).classes("lp-track-continue-btn")
                else:
                    ui.button("Continue course", on_click=on_view_course(course_id)).props("dense outline").classes(
                        "lp-track-continue-btn"
                    )

                overflow_menu = apply_icon_button_a11y(
                    ui.dropdown_button("", icon="more_horiz", auto_close=True)
                    .props("dense outline")
                    .classes("lp-home-row-overflow"),
                    label="Open tracking actions",
                    tooltip="Tracking actions",
                )
                with overflow_menu:

                    async def _clear_status_click(_cid: int = course_id) -> None:
                        await on_clear_status(_cid)

                    def _set_status_handler(*, key: str, cid: int) -> Any:
                        async def _run() -> None:
                            await on_set_status(cid, key)

                        return _run

                    ui.menu_item("View", on_click=on_view_course(course_id))
                    ui.menu_item("Review", on_click=on_review_course(course_id))
                    ui.separator()
                    ui.menu_item("Not tracked", on_click=_clear_status_click)
                    for key, label in TRACKING_STATUS_OPTIONS:
                        ui.menu_item(label, on_click=_set_status_handler(key=key, cid=course_id))

        with ui.row().classes("w-full items-center gap-2 lp-track-social-line"):
            with ui.row().classes("items-center gap-1"):
                ui.icon("person").classes("text-[12px] lp-home-track-meta")
                ui.icon("person").classes("text-[12px] lp-home-track-meta")
                ui.icon("person").classes("text-[12px] lp-home-track-meta")
            ui.label(f"{max(0, teammates_active)} teammates active").classes("text-xs lp-home-track-meta")

        with ui.row().classes(f"w-full items-center gap-2 lp-track-progress-meta {tone_class}"):
            ui.label(tracking_label_fn(status)).classes("text-xs lp-track-status-text")
            ui.linear_progress(float(progress_pct) / 100.0, show_value=False).classes(
                "grow lp-home-track-progress lp-track-progress-inline"
            )
            ui.label(f"{progress_pct}%").classes("text-xs font-semibold lp-home-track-progress-value")


def render_tracked_courses_section(
    *,
    tracked_courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    course_review_summary_by_id: dict[int, dict[str, Any]],
    tracked_visible: int,
    tracking_label_fn: Any,
    on_view_course: Any,
    on_review_course: Any,
    on_set_status: Any,
    on_clear_status: Any,
    on_browse_courses: Any,
) -> None:
    """Render tracked-courses card and rows."""
    card_classes = "lp-card w-full lp-home-track-shell"
    if not tracked_courses:
        card_classes += " lp-home-passive-empty"
    with ui.card().classes(card_classes):
        ui.label("Tracked courses").classes("lp-home-section-title lp-home-track-title")
        if not tracked_courses:
            ui.label("Track a course to see it here.").classes("text-sm lp-home-empty-copy").style("color: var(--lp-muted)")
            ui.button("Browse courses", on_click=on_browse_courses).props("dense outline").classes("lp-home-empty-btn")
            return

        ui.separator().classes("lp-home-track-separator")
        with ui.element("div").classes("lp-tracked-grid"):
            for idx, course in enumerate(tracked_courses[:tracked_visible]):
                _render_tracked_course_card(
                    index=idx,
                    course=course,
                    tracking_by_course_id=tracking_by_course_id,
                    course_review_summary_by_id=course_review_summary_by_id,
                    tracking_label_fn=tracking_label_fn,
                    on_view_course=on_view_course,
                    on_review_course=on_review_course,
                    on_set_status=on_set_status,
                    on_clear_status=on_clear_status,
                )


def render_selected_paths_section(
    *,
    selected_paths: list[dict[str, Any]],
    selected_visible: int,
    path_details_by_id: dict[int, dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    path_review_summary_by_id: dict[int, dict[str, Any]],
    progress_for_path_detail: Any,
    review_summary_label: Any,
    teammates_following: int,
    on_view_path: Any,
    on_browse_paths: Any,
) -> None:
    """Render selected-paths card and rows."""
    if not selected_paths:
        with ui.element("div").classes("w-full lp-home-path-empty-shell"):
            ui.label("Selected Path").classes("lp-home-section-title")
            ui.label("No path selected yet. Pick one path to track progress here.").classes("text-sm lp-home-empty-copy").style(
                "color: var(--lp-muted)"
            )
            ui.button("Browse paths", on_click=on_browse_paths).props("dense outline").classes("lp-home-empty-btn")
        return

    with ui.card().classes("lp-card w-full lp-home-path-shell"):
        ui.label("Selected Path").classes("lp-home-section-title")
        ui.separator().classes("lp-home-path-separator")
        for idx, row in enumerate(selected_paths[:selected_visible]):
            pid = int(row.get("id") or 0)
            detail = path_details_by_id.get(pid) or {}
            completed, total, ratio = progress_for_path_detail(
                detail=detail,
                tracking_by_course_id=tracking_by_course_id,
            )

            progress_pct = int(round(max(0.0, min(1.0, float(ratio))) * 100))
            card_tier_class = "lp-path-card--primary" if idx == 0 else "lp-path-card--secondary"

            with ui.element("div").classes(f"lp-track-card lp-path-card {card_tier_class} w-full"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-start gap-2"):
                        ui.icon("route").classes("lp-track-avatar")
                        with ui.column().classes("gap-0 lp-track-title-block"):
                            ui.label(str(row.get("name") or "")).classes("text-sm font-semibold")
                            ui.label(f"{completed} / {total} completed").classes("text-xs lp-home-track-meta").style(
                                "color: var(--lp-muted)"
                            )
                    with ui.row().classes("items-center gap-1 lp-track-actions"):
                        ui.button("Continue path", on_click=on_view_path(pid)).props("dense outline").classes(
                            "lp-track-continue-btn"
                        )

                review_badge = review_summary_label(path_review_summary_by_id.get(pid))
                with ui.row().classes("items-center gap-2 w-full lp-track-team-row"):
                    if teammates_following > 0:
                        with ui.row().classes("items-center gap-1"):
                            ui.icon("person").classes("text-[12px] lp-home-track-meta")
                            ui.icon("person").classes("text-[12px] lp-home-track-meta")
                        ui.label(f"{teammates_following} teammates also following").classes("text-xs lp-home-track-meta")
                    if review_badge:
                        ui.label(str(review_badge)).classes("text-xs lp-home-track-meta")

                ui.linear_progress(float(ratio), show_value=False).classes("w-full lp-home-track-progress")
                with ui.row().classes(
                    "w-full items-center gap-2 lp-home-track-status lp-track-status-line lp-home-status--active"
                ):
                    ui.label("Selected").classes("text-xs lp-track-status-text")
                    ui.linear_progress(float(ratio), show_value=False).classes(
                        "grow lp-home-track-progress lp-track-progress-inline"
                    )
                    ui.label(f"{progress_pct}%").classes("text-xs font-semibold lp-home-track-progress-value")


def render_shared_content(
    *,
    shared_learning_items: list[Any],
    shared_paths: list[dict[str, Any]],
    shared_path_review_summary_by_id: dict[int, dict[str, Any]],
    review_summary_label: Any,
    on_open_learning_item: Any,
    on_review_learning_item: Any,
    on_view_path: Any,
    on_review_path: Any,
) -> None:
    """Render shared tab content."""
    ui.label("You shared").classes("text-lg font-semibold mt-2")
    ui.label("Content you shared for others to discover.").classes("text-sm").style("color: var(--lp-muted)")

    with ui.card().classes("lp-card w-full lp-shared-shell"):
        ui.label("Learning items").classes("lp-home-section-title")
        ui.separator().classes("lp-shared-separator")
        if not shared_learning_items:
            ui.label("You haven't shared any learning items yet.").classes("text-sm lp-home-empty-copy").style(
                "color: var(--lp-muted)"
            )
        for item in shared_learning_items[:12]:
            item_type = str(item.item_type or "")
            item_icon = "play_circle" if item_type == "video" else ("article" if item_type == "article" else "school")
            with ui.element("div").classes("lp-track-card lp-shared-card"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-start gap-2 lp-track-identity"):
                        ui.icon(item_icon).classes("lp-track-avatar")
                        with ui.column().classes("gap-0 lp-track-title-block"):
                            ui.label(str(item.title or "")).classes("text-sm font-semibold lp-track-title")
                            ui.label(learning_item_type_label(item_type)).classes("text-xs lp-home-track-meta")
                    with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group"):
                        ui.button(
                            learning_item_primary_action_label(item_type),
                            on_click=on_open_learning_item(item),
                        ).props("dense outline").classes("lp-track-continue-btn")
                        if bool(getattr(item.capabilities, "supports_reviews", False)):
                            ui.button(
                                learning_item_review_action_label(item_type),
                                on_click=on_review_learning_item(item),
                            ).props("dense outline").classes("lp-track-continue-btn")
                parts = [review_summary_label(item.review_summary_row)]
                parts = [part for part in parts if part]
                if parts:
                    ui.label(" · ".join(parts)).classes("text-xs lp-home-track-meta lp-shared-meta-line").style(
                        "color: var(--lp-muted)"
                    )

    with ui.card().classes("lp-card w-full lp-shared-shell"):
        ui.label("Paths").classes("lp-home-section-title")
        ui.separator().classes("lp-shared-separator")
        if not shared_paths:
            ui.label("You haven't shared any paths yet.").classes("text-sm lp-home-empty-copy").style("color: var(--lp-muted)")
        for p in shared_paths[:12]:
            pid = int(p.get("id") or 0)
            with ui.element("div").classes("lp-track-card lp-shared-card"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-start gap-2 lp-track-identity"):
                        ui.icon("route").classes("lp-track-avatar")
                        with ui.column().classes("gap-0 lp-track-title-block"):
                            ui.label(str(p.get("name") or "")).classes("text-sm font-semibold lp-track-title")
                            ui.label("Path").classes("text-xs lp-home-track-meta")
                    with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group"):
                        ui.button("View", on_click=on_view_path(pid)).props("dense outline").classes("lp-track-continue-btn")
                        ui.button("Review", on_click=on_review_path(pid)).props("dense outline").classes(
                            "lp-track-continue-btn"
                        )
                parts = [review_summary_label(shared_path_review_summary_by_id.get(pid))]
                parts = [part for part in parts if part]
                if parts:
                    ui.label(" · ".join(parts)).classes("text-xs lp-home-track-meta lp-shared-meta-line").style(
                        "color: var(--lp-muted)"
                    )


def render_home_hero_panel(
    *,
    next_course: dict[str, Any] | None,
    teammates_progressing: int,
    reviews_count: int,
    on_join_discussion: Any,
    on_open_selected_paths: Any,
) -> None:
    """Render the redesigned Home hero with dominant next action."""
    with ui.card().classes("lp-card w-full lp-home-hero-panel lp-home-focus-shell"):
        with ui.column().classes("w-full gap-2"):
            ui.label("Next focus").classes("lp-home-hero-eyebrow")

        if next_course is None:
            ui.label("No active next step yet. Start by tracking a course.").classes("text-sm lp-home-empty-copy").style(
                "color: var(--lp-muted)"
            )
            ui.button("Browse courses", on_click=lambda: ui.navigate.to("/explore?tab=courses")).props("dense outline").classes(
                "lp-home-empty-btn"
            )
            return

        nxt = dict(next_course.get("course") or {})
        title = str(nxt.get("title") or "").strip() or "Continue your top track"
        ui.label(title).classes("lp-home-hero-heading")
        ui.label(f"{max(0, teammates_progressing)} active learners · {max(0, reviews_count)} reviews pending").classes(
            "text-xs lp-home-hero-meta"
        ).style("color: var(--lp-muted)")

        with ui.row().classes("w-full items-center justify-end gap-2 lp-home-hero-actions"):
            ui.button("Open conversation", on_click=on_join_discussion).props("dense flat no-caps").classes(
                "lp-home-hero-secondary"
            )
            url = str(nxt.get("url") or "").strip()
            if url:
                ui.button("Continue course", on_click=lambda u=url: ui.navigate.to(u, new_tab=True)).props(
                    "unelevated"
                ).classes("lp-home-hero-primary")
            elif int(next_course.get("path_id") or 0) > 0:
                ui.button("Continue path", on_click=on_open_selected_paths).props("unelevated").classes("lp-home-hero-primary")


def render_home_focus_queue_panel(
    *,
    pending_course_review_ids: list[int],
    pending_path_review_ids: list[int],
    selected_paths_count: int,
    tracked_courses_count: int,
    on_open_first_course_review: Any,
    on_open_first_path_review: Any,
    on_open_selected_paths: Any,
    on_open_tracked_courses: Any,
    on_browse_courses: Any,
) -> None:
    """Render compact next-step queue next to the home hero."""
    pending_reviews = len(pending_course_review_ids) + len(pending_path_review_ids)
    with ui.card().classes("lp-card w-full lp-home-focus-queue-panel lp-home-focus-shell"):
        with ui.column().classes("w-full gap-2"):
            ui.label("Your next actions").classes("lp-home-queue-title")
            with ui.column().classes("w-full gap-1 lp-home-action-stats"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label("Course/path reviews pending").classes("lp-home-action-stat-label")
                    ui.label(str(max(0, pending_reviews))).classes("lp-home-action-stat-value")
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label("Tracked courses").classes("lp-home-action-stat-label")
                    ui.label(str(max(0, tracked_courses_count))).classes("lp-home-action-stat-value")
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label("Selected paths").classes("lp-home-action-stat-label")
                    ui.label(str(max(0, selected_paths_count))).classes("lp-home-action-stat-value")

            async def _open_reviews_queue() -> None:
                if pending_course_review_ids:
                    await on_open_first_course_review()
                    return
                if pending_path_review_ids:
                    await on_open_first_path_review()
                    return
                ui.navigate.to("/teams")

            if pending_reviews > 0:
                ui.button("Review next", on_click=_open_reviews_queue).props("unelevated no-caps").classes(
                    "lp-home-focus-primary-action"
                )
            elif tracked_courses_count > 0:
                ui.button("Continue learning", on_click=on_open_tracked_courses).props("unelevated no-caps").classes(
                    "lp-home-focus-primary-action"
                )
            elif selected_paths_count > 0:
                ui.button("Continue path", on_click=on_open_selected_paths).props("unelevated no-caps").classes(
                    "lp-home-focus-primary-action"
                )
            else:
                ui.button("Browse courses", on_click=on_browse_courses).props("outline dense no-caps").classes(
                    "lp-home-focus-secondary-action"
                )


def render_team_snapshot_section(
    *,
    tracking_by_course_id: dict[int, dict[str, Any]],
    active_learners: int,
    shares_count: int,
    reviews_count: int,
    on_open_full_stats: Any,
) -> None:
    """Render compact team snapshot with minimal metrics and tiny sparkline."""
    interested, in_progress, completed = _tracking_status_counts(tracking_by_course_id=tracking_by_course_id)

    with ui.column().classes("w-full gap-2 lp-home-snapshot-panel lp-home-snapshot-shell"):
        ui.label("Team Activity").classes("lp-home-section-title")
        ui.label("Continue your skill building").classes("text-xs lp-home-track-meta")
        ui.separator().classes("lp-home-snapshot-separator")
        with ui.column().classes("w-full gap-1"):
            with ui.element("div").classes("lp-home-stat-grid"):
                for label, value in (
                    ("Active learners", active_learners),
                    ("Shares this week", shares_count),
                    ("Reviews posted", reviews_count),
                ):
                    with ui.element("div").classes("lp-home-stat-card"):
                        ui.label(str(value)).classes("lp-home-stat-value")
                        ui.label(label).classes("lp-home-stat-label")
            with ui.element("div").classes("w-full lp-home-team-chart-wrap"):
                ui.echart(
                    {
                        "grid": {"left": 0, "right": 0, "top": 4, "bottom": 0},
                        "xAxis": {"type": "category", "show": False, "data": ["M", "T", "W", "T", "F", "S", "S"]},
                        "yAxis": {"type": "value", "show": False},
                        "series": [
                            {
                                "type": "line",
                                "data": [
                                    max(0, interested),
                                    max(1, in_progress),
                                    max(0, completed),
                                    max(1, shares_count),
                                    max(0, reviews_count),
                                    max(0, in_progress),
                                    max(0, interested),
                                ],
                                "smooth": True,
                                "symbol": "none",
                                "lineStyle": {"width": 2, "color": "#69b3f2"},
                                "areaStyle": {"color": "rgba(105,179,242,0.12)"},
                            }
                        ],
                    }
                ).classes("w-full h-16 lp-home-team-chart")
        with ui.row().classes("w-full justify-end lp-home-team-chart-footer"):
            ui.button("Open stats", on_click=on_open_full_stats).props("dense flat")


def render_conversations_section(
    *,
    items: list[dict[str, Any]],
    pending_course_review_ids: list[int],
    pending_path_review_ids: list[int],
    on_open_item: Any,
    on_open_first_course_review: Any,
    on_open_first_path_review: Any,
) -> None:
    """Render social conversation queue with inline actions and review nudges."""
    total_pending_reviews = len(pending_course_review_ids) + len(pending_path_review_ids)
    with ui.column().classes("w-full gap-2 lp-home-recent-shell"):
        with ui.row().classes("items-center gap-1"):
            ui.icon("forum").classes("text-sm")
            ui.label("Conversations Needing You").classes("lp-home-section-title")
            ui.label(str(min(3, len(items)) + total_pending_reviews)).classes("lp-chip lp-chip--sky")
            if items:
                ui.label("").classes("lp-home-live-dot")
        ui.separator().classes("lp-home-recent-separator")

        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap lp-home-convo-summary"):
            with ui.row().classes("items-center gap-2 flex-wrap"):
                pending_label = (
                    f"{total_pending_reviews} course/path reviews waiting"
                    if total_pending_reviews > 0
                    else "No pending course/path reviews"
                )
                ui.label(pending_label).classes("text-xs lp-home-track-meta").style("color: var(--lp-muted)")
            if total_pending_reviews > 0:
                if pending_course_review_ids:
                    ui.button("Review next", on_click=on_open_first_course_review).props("dense outline")
                elif pending_path_review_ids:
                    ui.button("Review next", on_click=on_open_first_path_review).props("dense outline")

        if not items:
            empty_copy = (
                "No conversations are waiting right now. Start with your pending course or path reviews."
                if total_pending_reviews > 0
                else "No conversations are waiting right now. Share a learning item or path to start team activity."
            )
            ui.label(empty_copy).classes("text-sm lp-home-empty-copy").style("color: var(--lp-muted)")
            return

        for row in items[:3]:
            with ui.element("div").classes("lp-home-convo-row"):
                who = str(row.get("created_by") or "").strip() or "Teammate"
                who_display = who[:1].upper() + who[1:] if who else "Teammate"
                title = str(row.get("title") or "").strip() or "Shared an update"
                created_at = str(row.get("created_at") or "").strip()
                when_label = created_at[:10] if created_at else "recent"
                initials = "".join(part[:1] for part in who.split() if part)[:2].upper() or who[:2].upper() or "TM"

                with ui.row().classes("w-full items-start justify-between gap-2 lp-home-convo-main"):
                    with ui.row().classes("items-start gap-2"):
                        ui.label(initials).classes("lp-home-avatar-chip")
                        with ui.column().classes("gap-0"):
                            ui.label(who_display).classes("lp-home-convo-who")
                            ui.label("shared").classes("lp-home-convo-shared")
                            ui.label(title).classes("lp-home-convo-title")
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.label(when_label).classes("lp-home-convo-time")
                        ui.button("Open", on_click=lambda _row=dict(row): on_open_item(_row)).props(
                            "dense flat no-caps"
                        ).classes("lp-home-convo-open")


def render_shared_tab(
    *,
    shared_vm: Any,
    review_summary_label: Any,
    nav_actions: Any,
) -> None:
    """Compose shared-tab UI from the shared view-model."""
    render_shared_content(
        shared_learning_items=shared_vm.shared_learning_items,
        shared_paths=shared_vm.shared_paths,
        shared_path_review_summary_by_id=shared_vm.shared_path_review_summary_by_id,
        review_summary_label=review_summary_label,
        on_open_learning_item=lambda item: (
            nav_actions.make_article_view_action(int(item.item_id))
            if str(item.item_type or "") == "article"
            else (
                nav_actions.make_video_view_action(int(item.item_id))
                if str(item.item_type or "") == "video"
                else nav_actions.make_course_view_action(int(item.item_id))
            )
        ),
        on_review_learning_item=lambda item: (
            nav_actions.make_article_view_action(int(item.item_id))
            if str(item.item_type or "") == "article"
            else (
                nav_actions.make_video_review_action(int(item.item_id))
                if str(item.item_type or "") == "video"
                else nav_actions.make_course_review_action(int(item.item_id))
            )
        ),
        on_view_path=nav_actions.make_path_view_action,
        on_review_path=nav_actions.make_path_review_action,
    )


def render_learning_tab(*, ctx: LearningTabContext) -> None:
    """Compose learning-tab UI from the learning view-model."""
    learning_vm = ctx.learning_vm
    state = ctx.state
    next_course = ctx.next_course
    first_course_review_action = ctx.first_course_review_action
    first_path_review_action = ctx.first_path_review_action
    review_summary_label = ctx.review_summary_label
    tracking_label_fn = ctx.tracking_label_fn
    progress_for_path_detail = ctx.progress_for_path_detail
    nav_actions = ctx.nav_actions
    on_set_tracking_status = ctx.on_set_tracking_status
    on_clear_tracking_status = ctx.on_clear_tracking_status
    on_browse_courses = ctx.on_browse_courses
    on_browse_paths = ctx.on_browse_paths
    on_open_selected_paths = ctx.on_open_selected_paths
    on_open_full_stats = ctx.on_open_full_stats
    recently_shared_in_teams = ctx.recently_shared_in_teams
    on_open_recently_shared_item = ctx.on_open_recently_shared_item
    on_load_more_selected = ctx.on_load_more_selected

    teammate_usernames = sorted(
        {
            str(row.get("created_by") or "").strip()
            for row in recently_shared_in_teams
            if str(row.get("created_by") or "").strip()
        }
    )
    active_learners = max(1, len(teammate_usernames))
    shares_count = len(recently_shared_in_teams)
    reviews_count = len(learning_vm.pending_course_review_ids) + len(learning_vm.pending_path_review_ids)
    tracked_preview_visible = min(int(state.tracked_visible), 2)

    with ui.column().classes("w-full gap-4"):
        with ui.element("section").classes("lp-home-grid-12 lp-home-grid-top"):
            with ui.element("div").classes("lp-home-span-8"):
                render_home_hero_panel(
                    next_course=next_course,
                    teammates_progressing=active_learners,
                    reviews_count=reviews_count,
                    on_join_discussion=lambda: ui.navigate.to("/teams"),
                    on_open_selected_paths=on_open_selected_paths,
                )
            with ui.element("div").classes("lp-home-span-4"):
                render_home_focus_queue_panel(
                    pending_course_review_ids=learning_vm.pending_course_review_ids,
                    pending_path_review_ids=learning_vm.pending_path_review_ids,
                    selected_paths_count=len(learning_vm.selected_paths),
                    tracked_courses_count=len(learning_vm.tracked_courses),
                    on_open_first_course_review=first_course_review_action,
                    on_open_first_path_review=first_path_review_action,
                    on_open_selected_paths=on_open_selected_paths,
                    on_open_tracked_courses=on_browse_courses,
                    on_browse_courses=on_browse_courses,
                )

        with ui.element("section").classes("lp-home-grid-12 lp-home-grid-middle"):
            with ui.element("div").classes("lp-home-span-5 lp-home-col-stack"):
                render_tracked_courses_section(
                    tracked_courses=learning_vm.tracked_courses,
                    tracking_by_course_id=learning_vm.tracking_by_course_id,
                    course_review_summary_by_id=learning_vm.course_review_summary_by_id,
                    tracked_visible=tracked_preview_visible,
                    tracking_label_fn=tracking_label_fn,
                    on_view_course=nav_actions.make_course_view_action,
                    on_review_course=nav_actions.make_course_review_action,
                    on_set_status=on_set_tracking_status,
                    on_clear_status=on_clear_tracking_status,
                    on_browse_courses=on_browse_courses,
                )
                if len(learning_vm.tracked_courses) > tracked_preview_visible:
                    ui.button(
                        f"View all tracked courses ({len(learning_vm.tracked_courses)})",
                        on_click=on_browse_courses,
                    ).props("outline dense")
            with ui.element("div").classes("lp-home-span-4 lp-home-col-stack"):
                render_selected_paths_section(
                    selected_paths=learning_vm.selected_paths,
                    selected_visible=state.selected_visible,
                    path_details_by_id=learning_vm.path_details_by_id,
                    tracking_by_course_id=learning_vm.tracking_by_course_id,
                    path_review_summary_by_id=learning_vm.path_review_summary_by_id,
                    progress_for_path_detail=progress_for_path_detail,
                    review_summary_label=review_summary_label,
                    teammates_following=max(0, active_learners - 1),
                    on_view_path=nav_actions.make_path_view_action,
                    on_browse_paths=on_browse_paths,
                )
                if len(learning_vm.selected_paths) > state.selected_visible:
                    ui.button(
                        f"Load more ({state.selected_visible}/{len(learning_vm.selected_paths)})",
                        on_click=on_load_more_selected,
                    ).props("outline dense")
            with ui.element("div").classes("lp-home-span-3"):
                render_team_snapshot_section(
                    tracking_by_course_id=learning_vm.tracking_by_course_id,
                    active_learners=active_learners,
                    shares_count=shares_count,
                    reviews_count=reviews_count,
                    on_open_full_stats=on_open_full_stats,
                )

        with ui.element("section").classes("lp-home-grid-12 lp-home-grid-footer"):
            with ui.element("div").classes("lp-home-span-12 lp-home-col-stack"):
                render_conversations_section(
                    items=recently_shared_in_teams,
                    pending_course_review_ids=learning_vm.pending_course_review_ids,
                    pending_path_review_ids=learning_vm.pending_path_review_ids,
                    on_open_item=on_open_recently_shared_item,
                    on_open_first_course_review=first_course_review_action,
                    on_open_first_path_review=first_path_review_action,
                )
