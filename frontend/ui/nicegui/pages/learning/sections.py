"""UI sections for the Learning page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.status_chips import TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.errors import FrontendError, safe_notify


_ALLOWED_TRACKING_STATUSES = {"interested", "in_progress", "completed"}


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

    async def _on_status_change(e: Any, _cid: int = int(course_id), _select=status_select) -> None:
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
            for idx, c in enumerate(tracked_courses[:tracked_visible]):
                cid = int(c.get("id") or 0)
                tr = tracking_by_course_id.get(cid) or {}
                status = str(tr.get("status") or "")
                progress_pct = _tracked_progress_percent(status=status)
                tone_class = _tracked_status_tone(status=status)
                teammates_active = int((course_review_summary_by_id.get(cid) or {}).get("review_count") or 0)
                source_url = str(c.get("url") or "").strip()
                card_tier_class = "lp-track-card--primary" if idx == 0 else "lp-track-card--secondary"
                card_size_class = "lp-track-card--major" if idx == 0 else "lp-track-card--minor"

                with ui.element("div").classes(f"lp-track-card {card_tier_class} {card_size_class} w-full"):
                    with ui.row().classes("w-full items-start justify-between gap-3"):
                        with ui.row().classes("items-start gap-2 lp-track-identity"):
                            ui.icon("school").classes("lp-track-avatar")
                            with ui.column().classes("gap-0 lp-track-title-block"):
                                ui.label(str(c.get("title") or "")).classes("text-sm font-semibold lp-track-title")
                                provider = str(c.get("provider") or "").strip()
                                duration_raw = c.get("duration_hours")
                                duration = ""
                                try:
                                    duration_value = float(duration_raw)
                                    if duration_value > 0:
                                        duration = (
                                            f"{int(duration_value)}h"
                                            if duration_value.is_integer()
                                            else f"{duration_value:.1f}h"
                                        )
                                except (TypeError, ValueError):
                                    duration = ""
                                level = str(c.get("level") or "").strip()
                                bits = [b for b in [provider, duration, level] if b]
                                if bits:
                                    ui.label(" · ".join(bits)).classes("text-xs lp-home-track-meta").style(
                                        "color: var(--lp-muted)"
                                    )

                        with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group"):
                            if source_url:
                                ui.button("Continue", on_click=lambda u=source_url: ui.navigate.to(u, new_tab=True)).props(
                                    "dense outline"
                                ).classes("lp-track-continue-btn")
                            else:
                                ui.button("Continue", on_click=on_view_course(cid)).props("dense outline").classes(
                                    "lp-track-continue-btn"
                                )

                            with (
                                ui.dropdown_button("", icon="more_horiz", auto_close=True)
                                .props("dense outline")
                                .classes("lp-home-row-overflow")
                            ):

                                async def _clear_status_click(_cid: int = cid) -> None:
                                    await on_clear_status(_cid)

                                def _set_status_handler(*, key: str, course_id: int) -> Any:
                                    async def _run() -> None:
                                        await on_set_status(course_id, key)

                                    return _run

                                ui.menu_item("View", on_click=on_view_course(cid))
                                ui.menu_item("Review", on_click=on_review_course(cid))
                                ui.separator()
                                ui.menu_item("Not tracked", on_click=_clear_status_click)
                                for key, label in TRACKING_STATUS_OPTIONS:
                                    ui.menu_item(label, on_click=_set_status_handler(key=key, course_id=cid))

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
    card_classes = "lp-card w-full lp-home-path-shell"
    if not selected_paths:
        card_classes += " lp-home-passive-empty"
    with ui.card().classes(card_classes):
        ui.label("Selected paths").classes("lp-home-section-title")
        if not selected_paths:
            ui.label("Select a path to track progress.").classes("text-sm lp-home-empty-copy").style("color: var(--lp-muted)")
            ui.button("Browse paths", on_click=on_browse_paths).props("dense outline").classes("lp-home-empty-btn")
            return

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
    shared_courses: list[dict[str, Any]],
    shared_paths: list[dict[str, Any]],
    shared_articles: list[dict[str, Any]],
    shared_course_review_summary_by_id: dict[int, dict[str, Any]],
    shared_course_recommendation_summary_by_id: dict[int, dict[str, Any]],
    shared_path_review_summary_by_id: dict[int, dict[str, Any]],
    shared_path_recommendation_summary_by_id: dict[int, dict[str, Any]],
    review_summary_label: Any,
    recommendation_summary_label: Any,
    on_view_course: Any,
    on_review_course: Any,
    on_view_path: Any,
    on_review_path: Any,
    feature_articles: bool,
    on_open_articles: Any,
) -> None:
    """Render shared tab content."""
    ui.label("You shared").classes("text-lg font-semibold mt-2")
    ui.label("Content you shared with teammates.").classes("text-sm").style("color: var(--lp-muted)")

    with ui.card().classes("lp-card w-full lp-shared-shell"):
        ui.label("Courses").classes("lp-home-section-title")
        ui.separator().classes("lp-shared-separator")
        if not shared_courses:
            ui.label("You haven't shared any courses yet.").classes("text-sm lp-home-empty-copy").style(
                "color: var(--lp-muted)"
            )
        for c in shared_courses[:12]:
            cid = int(c.get("id") or 0)
            with ui.element("div").classes("lp-track-card lp-shared-card"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-start gap-2 lp-track-identity"):
                        ui.icon("school").classes("lp-track-avatar")
                        with ui.column().classes("gap-0 lp-track-title-block"):
                            ui.label(str(c.get("title") or "")).classes("text-sm font-semibold lp-track-title")
                            ui.label("Course").classes("text-xs lp-home-track-meta")
                    with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group"):
                        ui.button("View", on_click=on_view_course(cid)).props("dense outline").classes("lp-track-continue-btn")
                        ui.button("Review", on_click=on_review_course(cid)).props("dense outline").classes(
                            "lp-track-continue-btn"
                        )
                parts = [
                    review_summary_label(shared_course_review_summary_by_id.get(cid)),
                    recommendation_summary_label(shared_course_recommendation_summary_by_id.get(cid)),
                ]
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
                parts = [
                    review_summary_label(shared_path_review_summary_by_id.get(pid)),
                    recommendation_summary_label(shared_path_recommendation_summary_by_id.get(pid)),
                ]
                parts = [part for part in parts if part]
                if parts:
                    ui.label(" · ".join(parts)).classes("text-xs lp-home-track-meta lp-shared-meta-line").style(
                        "color: var(--lp-muted)"
                    )

    if feature_articles:
        with ui.card().classes("lp-card w-full lp-shared-shell"):
            ui.label("Articles").classes("lp-home-section-title")
            ui.separator().classes("lp-shared-separator")
            if not shared_articles:
                ui.label("You haven't shared any articles yet.").classes("text-sm lp-home-empty-copy").style(
                    "color: var(--lp-muted)"
                )
            for a in shared_articles[:12]:
                with ui.element("div").classes("lp-track-card lp-shared-card"):
                    with ui.row().classes("w-full items-center justify-between gap-3"):
                        with ui.row().classes("items-center gap-2 lp-track-identity"):
                            ui.icon("article").classes("lp-track-avatar")
                            ui.label(str(a.get("title") or "")).classes("text-sm font-semibold lp-track-title")
                        ui.button("Open", on_click=on_open_articles).props("dense outline").classes("lp-track-continue-btn")


def render_home_hero_panel(
    *,
    next_course: dict[str, Any] | None,
    teammates_progressing: int,
    new_comments_count: int,
    reviews_count: int,
    teammate_usernames: list[str],
    on_join_discussion: Any,
    on_open_selected_paths: Any,
) -> None:
    """Render the redesigned Home hero with dominant next action."""
    with ui.card().classes("lp-card w-full lp-home-hero-panel lp-home-focus-shell"):
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("items-center gap-1"):
                ui.icon("local_fire_department").classes("text-sm")
                ui.label("Team Learning Momentum").classes("lp-home-hero-eyebrow")

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
        ui.label(title).classes("text-lg font-semibold")
        ui.label(
            f"{max(0, teammates_progressing)} active learners · {max(0, new_comments_count)} new comments · {max(0, reviews_count)} reviews"
        ).classes("text-xs lp-home-track-meta").style("color: var(--lp-muted)")
        if teammates_progressing > 0:
            ui.label(f"{teammates_progressing} teammates progressing").classes("text-xs lp-home-track-meta").style(
                "color: var(--lp-muted)"
            )

        if teammate_usernames:
            with ui.row().classes("items-center gap-1"):
                for teammate in teammate_usernames[:3]:
                    initials = "".join(part[:1] for part in teammate.split() if part)[:2].upper() or teammate[:2].upper()
                    ui.label(initials).classes("lp-home-avatar-chip")

        with ui.row().classes("w-full items-center justify-end gap-2"):
            ui.button("Open reviews", on_click=on_join_discussion).props("dense outline")
            url = str(nxt.get("url") or "").strip()
            if url:
                ui.button("Continue", on_click=lambda u=url: ui.navigate.to(u, new_tab=True)).props("unelevated")
            elif int(next_course.get("path_id") or 0) > 0:
                ui.button("Continue", on_click=on_open_selected_paths).props("unelevated")


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
        ui.label("Team Snapshot").classes("lp-home-section-title")
        ui.separator().classes("lp-home-snapshot-separator")
        with ui.column().classes("w-full gap-1"):
            for label, value in (
                ("Active learners", active_learners),
                ("Shares this week", shares_count),
                ("Reviews posted", reviews_count),
            ):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(label).classes("text-xs lp-home-track-meta")
                    ui.label(str(value)).classes("text-sm font-semibold")
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
            ).classes("w-full h-14")
        with ui.row().classes("w-full justify-end"):
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
    with ui.column().classes("w-full lp-home-flat-section"):
        with ui.row().classes("items-center gap-1"):
            ui.icon("forum").classes("text-sm")
            ui.label("Conversations Needing You").classes("lp-home-section-title")
            ui.label(str(min(3, len(items)) + total_pending_reviews)).classes("lp-chip lp-chip--sky")
        ui.separator().classes("lp-home-recent-separator")

        with ui.row().classes("items-center gap-2 flex-wrap"):
            ui.label(f"Courses: {len(pending_course_review_ids)}").classes("lp-chip lp-chip--muted")
            ui.label(f"Paths: {len(pending_path_review_ids)}").classes("lp-chip lp-chip--muted")
            if total_pending_reviews > 0:
                ui.label(f"{total_pending_reviews} reviews waiting").classes("text-xs lp-home-track-meta").style(
                    "color: var(--lp-muted)"
                )

        if not items:
            empty_copy = (
                "No conversations pending right now. You still have reviews waiting."
                if total_pending_reviews > 0
                else "No conversations or reviews pending right now."
            )
            ui.label(empty_copy).classes("text-sm lp-home-empty-copy").style("color: var(--lp-muted)")
            if total_pending_reviews > 0:
                with ui.row().classes("w-full justify-end"):
                    if pending_course_review_ids:
                        ui.button("Review next", on_click=on_open_first_course_review).props("dense outline")
                    elif pending_path_review_ids:
                        ui.button("Review next", on_click=on_open_first_path_review).props("dense outline")
            return

        for row in items[:3]:
            with ui.element("div").classes("lp-home-track-row"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    with ui.row().classes("items-center gap-2"):
                        who = str(row.get("created_by") or "").strip()
                        initials = "".join(part[:1] for part in who.split() if part)[:2].upper() or who[:2].upper() or "TM"
                        ui.label(initials).classes("lp-home-avatar-chip")
                        ui.label(f"{who} shared {str(row.get('title') or '')}").classes("text-sm")
                    ui.label("1h ago").classes("text-xs lp-home-track-meta")
                with ui.row().classes("w-full justify-end"):
                    ui.button("Reply", on_click=lambda _row=dict(row): on_open_item(_row)).props("dense outline")

        if total_pending_reviews > 0:
            with ui.row().classes("w-full justify-end"):
                if pending_course_review_ids:
                    ui.button("Review next", on_click=on_open_first_course_review).props("dense outline")
                elif pending_path_review_ids:
                    ui.button("Review next", on_click=on_open_first_path_review).props("dense outline")


def render_shared_tab(
    *,
    shared_vm: Any,
    review_summary_label: Any,
    recommendation_summary_label: Any,
    nav_actions: Any,
    feature_articles: bool,
    on_open_articles: Any,
) -> None:
    """Compose shared-tab UI from the shared view-model."""
    render_shared_content(
        shared_courses=shared_vm.shared_courses,
        shared_paths=shared_vm.shared_paths,
        shared_articles=shared_vm.shared_articles,
        shared_course_review_summary_by_id=shared_vm.shared_course_review_summary_by_id,
        shared_course_recommendation_summary_by_id=shared_vm.shared_course_recommendation_summary_by_id,
        shared_path_review_summary_by_id=shared_vm.shared_path_review_summary_by_id,
        shared_path_recommendation_summary_by_id=shared_vm.shared_path_recommendation_summary_by_id,
        review_summary_label=review_summary_label,
        recommendation_summary_label=recommendation_summary_label,
        on_view_course=nav_actions.make_course_view_action,
        on_review_course=nav_actions.make_course_review_action,
        on_view_path=nav_actions.make_path_view_action,
        on_review_path=nav_actions.make_path_review_action,
        feature_articles=bool(feature_articles),
        on_open_articles=on_open_articles,
    )


def render_learning_tab(
    *,
    learning_vm: Any,
    state: Any,
    next_course: dict[str, Any] | None,
    first_course_review_action: Any,
    first_path_review_action: Any,
    review_summary_label: Any,
    tracking_label_fn: Any,
    progress_for_path_detail: Any,
    nav_actions: Any,
    on_set_tracking_status: Any,
    on_clear_tracking_status: Any,
    on_browse_courses: Any,
    on_browse_paths: Any,
    on_open_selected_paths: Any,
    on_open_full_stats: Any,
    recently_shared_in_teams: list[dict[str, Any]],
    on_open_recently_shared_item: Any,
    on_load_more_tracked: Any,
    on_load_more_selected: Any,
) -> None:
    """Compose learning-tab UI from the learning view-model."""
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
    new_comments_count = max(0, min(8, shares_count * 2))

    with ui.column().classes("w-full gap-4"):
        with ui.element("section").classes("lp-home-row-grid lp-home-row-grid--single"):
            render_home_hero_panel(
                next_course=next_course,
                teammates_progressing=active_learners,
                new_comments_count=new_comments_count,
                reviews_count=reviews_count,
                teammate_usernames=teammate_usernames,
                on_join_discussion=lambda: ui.navigate.to("/teams"),
                on_open_selected_paths=on_open_selected_paths,
            )

        with ui.element("section").classes("lp-home-row-grid lp-home-row-grid--social"):
            render_conversations_section(
                items=recently_shared_in_teams,
                pending_course_review_ids=learning_vm.pending_course_review_ids,
                pending_path_review_ids=learning_vm.pending_path_review_ids,
                on_open_item=on_open_recently_shared_item,
                on_open_first_course_review=first_course_review_action,
                on_open_first_path_review=first_path_review_action,
            )
            render_team_snapshot_section(
                tracking_by_course_id=learning_vm.tracking_by_course_id,
                active_learners=active_learners,
                shares_count=shares_count,
                reviews_count=reviews_count,
                on_open_full_stats=on_open_full_stats,
            )

        render_tracked_courses_section(
            tracked_courses=learning_vm.tracked_courses,
            tracking_by_course_id=learning_vm.tracking_by_course_id,
            course_review_summary_by_id=learning_vm.course_review_summary_by_id,
            tracked_visible=state.tracked_visible,
            tracking_label_fn=tracking_label_fn,
            on_view_course=nav_actions.make_course_view_action,
            on_review_course=nav_actions.make_course_review_action,
            on_set_status=on_set_tracking_status,
            on_clear_status=on_clear_tracking_status,
            on_browse_courses=on_browse_courses,
        )
        if len(learning_vm.tracked_courses) > state.tracked_visible:
            ui.button(
                f"Load more ({state.tracked_visible}/{len(learning_vm.tracked_courses)})",
                on_click=on_load_more_tracked,
            ).props("outline dense")

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
