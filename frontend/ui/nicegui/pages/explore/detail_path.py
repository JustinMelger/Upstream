"""Path detail route renderer for Explore."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.courses.ui_glue import format_short_date
from frontend.ui.nicegui.pages.explore.detail_common import (
    parse_detail_id,
    parse_path_course_ids,
    parse_view_mode,
    render_breadcrumb,
    render_detail_scope,
)
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.dialogs import open_edit_path_dialog


async def render_explore_path_detail_page(*, store: SessionStore, api: ApiClient, path_id: str) -> None:
    """Render dedicated Explore path detail route."""
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    is_admin = str(user.get("role") or "") == "admin"
    view_mode = parse_view_mode()
    pid = parse_detail_id(path_id)

    with render_detail_scope(store=store, api=api):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        ui.element("div").classes("h-2")
        render_breadcrumb(label="Paths")
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
        courses = [c for c in list(detail.get("courses") or []) if isinstance(c, dict)]
        can_edit = bool(is_admin or (str(detail.get("created_by") or "").strip() == username))

        with ui.row().classes("w-full items-start gap-4"):
            with ui.column().classes("lp-explore-detail-main"):
                ui.label(str(detail.get("name") or "Path")).classes("lp-explore-detail-title")
                if str(detail.get("description") or "").strip():
                    ui.label(str(detail.get("description") or "")).classes("lp-explore-detail-body")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    if str(detail.get("created_by") or "").strip():
                        ui.label(f"Shared by {detail.get('created_by')}").classes("lp-meta-chip lp-meta-chip--quiet")
                    ui.label(f"{len(courses)} courses").classes("lp-meta-chip")

                if view_mode != "reviews":
                    ui.label("Path sequence").classes("text-base font-semibold mt-2")
                    for idx, row in enumerate(courses, start=1):
                        ui.label(f"{idx}. {str(row.get('title') or 'Course')}").classes("lp-explore-detail-muted")

                render_reviews_panel(
                    username=username,
                    is_admin=is_admin,
                    reviews=list(bundle.path_reviews or []),
                    on_save=lambda rating, text: controller.save_path_review(
                        path_id=pid, rating=int(rating), text=str(text or "")
                    ),
                    on_delete=lambda review_id: controller.delete_path_review(path_id=pid, review_id=int(review_id)),
                    hooks=ReviewPanelHooks(format_date=format_short_date),
                )

            with ui.column().classes("lp-explore-detail-side"):
                ui.label("Actions").classes("text-sm font-semibold")
                ui.button("Manage in Paths", on_click=lambda: ui.navigate.to(f"/manage/paths?path_id={pid}")).props("outline")
                if can_edit:

                    @guard_ui_action(title="Open edit failed")
                    async def _open_edit_path() -> None:
                        detail_row = await controller.get_path_detail(path_id=pid)
                        courses_rows = list(await api.get("/courses") or [])
                        course_by_id: dict[int, dict[str, Any]] = {}
                        for row in courses_rows:
                            if not isinstance(row, dict):
                                continue
                            try:
                                rid = int(row.get("id") or 0)
                            except (TypeError, ValueError):
                                continue
                            if rid > 0:
                                course_by_id[rid] = row

                        async def _save(payload: dict[str, Any]) -> None:
                            await controller.update_path(path_id=pid, payload=dict(payload or {}))
                            ui.navigate.to(f"/explore/paths/{pid}")

                        await open_edit_path_dialog(
                            detail=detail_row,
                            course_by_id=course_by_id,
                            detail_dialog=None,
                            on_save=_save,
                        )

                    ui.button("Edit", icon="edit", on_click=_open_edit_path).props("outline")

                ui.separator()
                ui.label("Resources").classes("text-sm font-semibold")
                for cid in parse_path_course_ids(detail)[:6]:
                    ui.link(f"Course {cid}", f"/explore/courses/{cid}")
