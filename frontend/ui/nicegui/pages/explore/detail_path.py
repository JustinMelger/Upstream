"""Path detail route renderer for Explore."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.path_items import encode_path_item_ref, learning_item_option_label
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.domains.courses.ui_glue import format_short_date
from frontend.ui.nicegui.domains.paths.controller import PathsPageController
from frontend.ui.nicegui.domains.paths.dialogs import open_edit_path_dialog
from frontend.ui.nicegui.pages.explore.detail_common import (
    parse_detail_id,
    render_breadcrumb,
    render_detail_scope,
)
from frontend.ui.nicegui.services.paths_service import select_path_and_seed_tracking


@dataclass(frozen=True, slots=True)
class PathMainPanelContext:
    controller: PathsPageController
    pid: int
    username: str
    is_admin: bool
    detail: dict[str, Any]
    items: list[dict[str, Any]]
    courses: list[dict[str, Any]]
    path_reviews: list[dict[str, Any]]
    tracking_by_course_id: dict[int, dict[str, Any]]
    is_selected: bool


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _course_status(*, course: dict[str, Any], tracking_by_course_id: dict[int, dict[str, Any]]) -> str:
    cid = _safe_int(course.get("id"))
    tracked = tracking_by_course_id.get(cid)
    if isinstance(tracked, dict):
        return str(tracked.get("status") or "").strip().lower()
    return str(course.get("tracking_status") or "").strip().lower()


def _path_progress(
    *,
    courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> tuple[int, int, float]:
    total = len(courses)
    if total <= 0:
        return 0, 0, 0.0
    completed = 0
    for row in courses:
        if _course_status(course=row, tracking_by_course_id=tracking_by_course_id) == "completed":
            completed += 1
    return completed, total, max(0.0, min(1.0, float(completed) / float(total)))


def _path_item_type(item: dict[str, Any]) -> str:
    return str(item.get("type") or "course").strip().lower() or "course"


def _path_item_route(item: dict[str, Any]) -> str:
    item_type = _path_item_type(item)
    item_id = _safe_int(item.get("id"))
    if item_type == "article":
        return f"/explore/articles/{item_id}"
    if item_type == "video":
        return f"/explore/videos/{item_id}"
    return f"/explore/courses/{item_id}"


def _path_duration_range(*, courses: list[dict[str, Any]]) -> str:
    durations = [_safe_float(row.get("duration_hours")) for row in courses if _safe_float(row.get("duration_hours")) > 0]
    if not durations:
        return ""
    if len(durations) == 1:
        return f"{durations[0]:.1f}h".replace(".0h", "h")
    return f"{min(durations):.1f}–{max(durations):.1f} hours".replace(".0", "")


def _avg_rating(*, reviews: list[dict[str, Any]]) -> tuple[float, int]:
    values: list[int] = []
    for row in reviews:
        rating = _safe_int(row.get("rating"))
        if 1 <= rating <= 5:
            values.append(rating)
    if not values:
        return 0.0, 0
    return float(sum(values)) / float(len(values)), len(values)


def _stars(*, avg: float) -> str:
    rounded = max(0, min(5, int(round(float(avg)))))
    return ("★" * rounded) + ("☆" * (5 - rounded))


def _render_path_sequence_card(
    *,
    items: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> None:
    with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface lp-path-sequence-card"):
        ui.label("Path Sequence").classes("text-base font-semibold")
        ui.label("Follow the steps to complete the path.").classes("lp-explore-detail-muted")
        if not items:
            ui.label("No learning items in this path yet.").classes("lp-explore-detail-muted")
            return
        with ui.column().classes("w-full gap-2"):
            for idx, row in enumerate(items, start=1):
                _render_path_sequence_item(idx=idx, row=row, tracking_by_course_id=tracking_by_course_id)


def _render_path_sequence_item(
    *,
    idx: int,
    row: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> None:
    """Render one typed learning-item row in the path sequence."""
    item_type = _path_item_type(row)
    cid = _safe_int(row.get("id"))
    title = str(row.get("title") or f"{item_type.title()} {idx}").strip()
    level = str(row.get("level") or row.get("difficulty") or "").strip()
    duration = _safe_float(row.get("duration_hours"))
    status = _course_status(course=row, tracking_by_course_id=tracking_by_course_id) if item_type == "course" else ""
    status_label = {
        "completed": "Completed",
        "in_progress": "In progress",
        "interested": "Tracked",
    }.get(status, "Not tracked")
    with ui.element("div").classes("lp-path-sequence-item w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label(title).classes("text-base")
                meta_bits = _path_sequence_meta_bits(item_type=item_type, duration=duration, level=level)
                if meta_bits:
                    ui.label(" • ".join(meta_bits)).classes("lp-explore-detail-muted")
            _render_path_sequence_action(item_type=item_type, cid=cid, row=row, status=status)
        _render_path_sequence_progress(item_type=item_type, status=status, status_label=status_label)


def _path_sequence_meta_bits(*, item_type: str, duration: float, level: str) -> list[str]:
    """Build compact meta text for a path sequence row."""
    meta_bits = [item_type.title()]
    if duration > 0:
        meta_bits.append(f"{duration:.1f}h".replace(".0h", "h"))
    if level:
        meta_bits.append(level)
    return meta_bits


def _render_path_sequence_action(*, item_type: str, cid: int, row: dict[str, Any], status: str) -> None:
    """Render the right-side action for one path sequence row."""
    if item_type != "course":
        ui.button("Open item", on_click=lambda _row=dict(row): ui.navigate.to(_path_item_route(_row))).props("outline dense")
        return
    if status == "completed":
        ui.label("✓ Completed").classes("lp-chip lp-chip--lime")
        return
    if status == "in_progress":
        ui.button("Continue course", on_click=lambda _cid=cid: ui.navigate.to(f"/explore/courses/{_cid}")).props("dense")
        return
    ui.button("Start course", on_click=lambda _cid=cid: ui.navigate.to(f"/explore/courses/{_cid}")).props("outline dense")


def _render_path_sequence_progress(*, item_type: str, status: str, status_label: str) -> None:
    """Render the progress/status line for one path sequence row."""
    if item_type != "course":
        ui.linear_progress(0.0, show_value=False).classes("w-full")
        ui.label("Reference step").classes("lp-explore-detail-muted")
        return
    if status == "in_progress":
        ui.linear_progress(0.55, show_value=False).classes("w-full")
    elif status == "completed":
        ui.linear_progress(1.0, show_value=False).classes("w-full")
    else:
        ui.linear_progress(0.0, show_value=False).classes("w-full")
    ui.label(status_label).classes("lp-explore-detail-muted")


def _render_path_main_panel(
    *,
    panel: PathMainPanelContext,
) -> None:
    completed, total, progress = _path_progress(courses=panel.courses, tracking_by_course_id=panel.tracking_by_course_id)
    duration_range = _path_duration_range(courses=panel.courses)
    avg_rating, review_count = _avg_rating(reviews=panel.path_reviews)
    panel_avg_rating = float(avg_rating)
    panel_review_count = int(review_count)

    with ui.column().classes("lp-explore-detail-main"):
        with ui.element("header").classes("lp-explore-detail-hero"):
            ui.label("Learning Path").classes("lp-explore-detail-eyebrow")
            ui.label(str(panel.detail.get("name") or "Path")).classes("lp-explore-detail-title")
            description = str(panel.detail.get("description") or "").strip()
            if description:
                ui.label(description).classes("lp-explore-detail-body")

        with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(str(panel.detail.get("name") or "Path")).classes("text-lg font-semibold")
                ui.label("Tracked" if panel.is_selected else "Not tracked").classes(
                    "lp-chip lp-chip--teal" if panel.is_selected else "lp-chip lp-chip--muted"
                )
            bits = [f"{len(panel.items)} learning items"]
            level = str(panel.detail.get("level") or panel.detail.get("difficulty") or "").strip()
            if level:
                bits.append(level)
            if duration_range:
                bits.append(duration_range)
            ui.label(" • ".join(bits)).classes("lp-explore-detail-muted")
            with ui.row().classes("w-full items-center justify-between mt-1"):
                with ui.column().classes("gap-1 flex-1"):
                    ui.label(f"Progress {completed} / {total} courses completed").classes("text-sm")
                    ui.linear_progress(progress, show_value=False).classes("w-full")
                ui.button(
                    "Continue Path" if completed > 0 else "Start Path",
                    on_click=lambda: ui.navigate.to(f"/explore/paths/{panel.pid}"),
                ).props("dense")

        _render_path_sequence_card(items=panel.items, tracking_by_course_id=panel.tracking_by_course_id)

        with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface lp-explore-reviews-panel"):

            @ui.refreshable
            def _review_summary() -> None:
                with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                    if panel_review_count > 0:
                        ui.label(_stars(avg=panel_avg_rating)).classes("lp-explore-rating-stars")
                        ui.label(f"{panel_avg_rating:.1f}").classes("lp-explore-rating-score")
                        ui.label(f"{panel_review_count} review{'s' if panel_review_count != 1 else ''}").classes(
                            "lp-explore-detail-muted"
                        )
                    else:
                        ui.label("No reviews yet").classes("lp-explore-detail-muted")

            def _handle_reviews_changed(updated_reviews: list[dict[str, Any]]) -> None:
                nonlocal panel_avg_rating, panel_review_count
                panel_avg_rating, panel_review_count = _avg_rating(reviews=updated_reviews)
                _review_summary.refresh()

            _review_summary()
            render_reviews_panel(
                username=panel.username,
                is_admin=panel.is_admin,
                reviews=panel.path_reviews,
                on_save=lambda rating, text: panel.controller.save_path_review(
                    path_id=panel.pid, rating=int(rating), text=str(text or "")
                ),
                on_delete=lambda review_id: panel.controller.delete_path_review(path_id=panel.pid, review_id=int(review_id)),
                hooks=ReviewPanelHooks(format_date=format_short_date, on_changed=_handle_reviews_changed),
            )


def _render_path_info_panel(
    *,
    controller: PathsPageController,
    api: ApiClient,
    pid: int,
    detail: dict[str, Any],
    items: list[dict[str, Any]],
    can_edit: bool,
    is_selected: bool,
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> None:
    with ui.column().classes("lp-explore-detail-side lp-explore-info-card"):
        ui.label("Path Actions").classes("text-base font-semibold")

        @guard_ui_action(title="Toggle path tracking failed")
        async def _toggle_path_tracking() -> None:
            if is_selected:
                await api.post(f"/paths/{pid}/unselect", {})
                safe_notify("Path untracked", type="positive")
            else:
                await select_path_and_seed_tracking(
                    api=api,
                    path_id=int(pid),
                    tracking_by_course_id=tracking_by_course_id,
                    cached_detail=detail,
                )
                safe_notify("Path tracked", type="positive")
            ui.navigate.to(f"/explore/paths/{pid}")

        ui.button("Track Path" if not is_selected else "Untrack Path", icon="checklist", on_click=_toggle_path_tracking).props(
            "outline"
        )
        ui.button(
            "Share Path",
            icon="share",
            on_click=lambda: copy_text_to_clipboard(
                text=f"/explore/paths/{pid}",
                success_message=f"Path link copied: /explore/paths/{pid}",
            ),
        ).props("outline")

        ui.separator()
        ui.label("Resources").classes("text-sm font-semibold")
        for row in items[:6]:
            item_id = _safe_int(row.get("id"))
            title = str(row.get("title") or f"Item {item_id}").strip()
            ui.link(title, _path_item_route(row)).classes("lp-explore-detail-muted")

        if can_edit:
            ui.separator()
            ui.label("Admin").classes("text-sm font-semibold")

            @guard_ui_action(title="Open edit failed")
            async def _open_edit_path() -> None:
                detail_row = await controller.get_path_detail(path_id=pid)
                courses_rows = [row for row in list(await api.get("/courses") or []) if isinstance(row, dict)]
                videos_rows = [row for row in list(await api.get("/videos") or []) if isinstance(row, dict)]
                articles_rows = [row for row in list(await api.get("/articles") or []) if isinstance(row, dict)]
                learning_item_options: dict[str, str] = {}
                for row in courses_rows:
                    rid = _safe_int(row.get("id"))
                    if rid > 0:
                        learning_item_options[encode_path_item_ref(item_type="course", item_id=rid)] = (
                            learning_item_option_label(item_type="course", row=row)
                        )
                for row in videos_rows:
                    rid = _safe_int(row.get("id"))
                    if rid > 0:
                        learning_item_options[encode_path_item_ref(item_type="video", item_id=rid)] = (
                            learning_item_option_label(item_type="video", row=row)
                        )
                for row in articles_rows:
                    rid = _safe_int(row.get("id"))
                    if rid > 0:
                        learning_item_options[encode_path_item_ref(item_type="article", item_id=rid)] = (
                            learning_item_option_label(item_type="article", row=row)
                        )

                async def _save(payload: dict[str, Any]) -> None:
                    await controller.update_path(path_id=pid, payload=dict(payload or {}))
                    ui.navigate.to(f"/explore/paths/{pid}")

                await open_edit_path_dialog(
                    detail=detail_row,
                    learning_item_options=learning_item_options,
                    detail_dialog=None,
                    on_save=_save,
                )

            @guard_ui_action(title="Delete path failed")
            async def _delete_path() -> None:
                await controller.delete_path(path_id=pid)
                safe_notify("Path deleted", type="positive")
                ui.navigate.to("/explore?tab=paths")

            ui.button("Edit", icon="edit", on_click=_open_edit_path).props("outline")
            ui.button("Delete", icon="delete", on_click=_delete_path).props("outline color=negative")


async def render_explore_path_detail_page(*, store: SessionStore, api: ApiClient, path_id: str) -> None:
    """Render dedicated Explore path detail route."""
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    is_admin = str(user.get("role") or "") == "admin"
    pid = parse_detail_id(path_id)

    with render_detail_scope(store=store, api=api):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        ui.element("div").classes("h-2")
        render_breadcrumb(label="Learning Path", back_url="/explore?tab=paths")
        if pid <= 0:
            ui.label("Invalid path id").classes("text-sm")
            return

        controller = PathsPageController(api=api)
        try:
            bundle = await controller.load_path_detail_bundle(path_id=pid)
        except ApiError as exc:
            ui.label(f"Path unavailable ({exc.status_code})").classes("text-sm")
            return

        detail = dict(bundle.detail or {})
        items = [row for row in list(detail.get("items") or []) if isinstance(row, dict)]
        courses = [row for row in items if str(row.get("type") or "") == "course"]
        can_edit = bool(is_admin or (str(detail.get("created_by") or "").strip() == username))
        path_reviews = list(bundle.path_reviews or [])
        selected_rows = await api.get("/paths/selected/list")
        selected_ids = {_safe_int(row.get("id")) for row in list(selected_rows or []) if isinstance(row, dict)}
        is_selected = int(pid) in selected_ids
        tracking_rows = await api.get("/tracking")
        tracking_by_course_id: dict[int, dict[str, Any]] = {}
        for row in list(tracking_rows or []):
            if not isinstance(row, dict):
                continue
            cid = _safe_int(row.get("course_id"))
            if cid > 0:
                tracking_by_course_id[cid] = row

        with ui.row().classes("w-full items-start gap-4 lp-refresh-region"):
            _render_path_main_panel(
                panel=PathMainPanelContext(
                    controller=controller,
                    pid=pid,
                    username=username,
                    is_admin=is_admin,
                    detail=detail,
                    items=items,
                    courses=courses,
                    path_reviews=path_reviews,
                    tracking_by_course_id=tracking_by_course_id,
                    is_selected=is_selected,
                ),
            )
            _render_path_info_panel(
                controller=controller,
                api=api,
                pid=pid,
                detail=detail,
                items=items or courses,
                can_edit=can_edit,
                is_selected=is_selected,
                tracking_by_course_id=tracking_by_course_id,
            )
