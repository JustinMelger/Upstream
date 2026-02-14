"""My Paths page for the NiceGUI frontend."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import status_chip_class, status_label, STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.paths_service import load_my_paths_page_data


def _format_review_summary(row: dict[str, Any] | None) -> str:
    """Format a review summary row into a compact label."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    return f"{avg:.1f}/5 ({count})"


def _filter_selected_paths(selected: list[dict[str, Any]] | None, *, needle: str, status: str) -> list[dict[str, Any]]:
    """Filter selected paths by name substring and optional status."""
    shown = list(selected or [])
    if needle:
        n = needle.strip().lower()
        if n:
            shown = [p for p in shown if n in str(p.get("name") or "").lower()]
    if status:
        shown = [p for p in shown if str(p.get("status") or "") == status]
    return shown


def _show_path_details_dialog(
    *,
    detail: dict[str, Any],
    selected_row: dict[str, Any],
    on_update_status: Callable[[str], Awaitable[None]],
    on_unselect: Callable[[], Awaitable[None]],
) -> None:
    """Open a dialog showing path details and allowing status/unselect actions.

    Args:
        detail: Path detail payload from the API (includes `courses`).
        selected_row: The selected-path row for this path (includes `status`).
        on_update_status: Callback invoked with the chosen status.
        on_unselect: Callback invoked to remove the path from "My Paths".
    """
    with ui.dialog() as dialog, ui.card().classes("w-[min(900px,95vw)]"):
        ui.label(detail.get("name") or "").classes("text-xl font-semibold")
        ui.label(detail.get("description") or "").classes("text-sm text-gray-600")

        ui.label(f"Status: {status_label(str(selected_row.get('status') or ''))}").classes("text-sm")

        status_select = ui.select(
            options={k: v for k, v in STATUS_OPTIONS},
            value=str(selected_row.get("status") or "interested"),
            label="Status",
        )

        courses_rows = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
        ui.separator()
        ui.label("Courses").classes("text-lg font-semibold")
        ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "title", "label": "Title", "field": "title"},
                {"name": "provider", "label": "Provider", "field": "provider"},
                {"name": "category", "label": "Category", "field": "category"},
                {"name": "level", "label": "Level", "field": "level"},
                {"name": "reviews", "label": "Reviews", "field": "reviews"},
            ],
            rows=courses_rows,
        ).classes("w-full")

        with ui.row().classes("justify-end mt-4"):
            update_btn = ui.button("Update status").props("outline")

            async def _update() -> None:
                update_btn.disable()
                try:
                    await on_update_status(str(status_select.value or ""))
                finally:
                    update_btn.enable()

            update_btn.on_click(_update)

            async def _remove() -> None:
                await on_unselect()
                dialog.close()

            ui.button("Unselect", on_click=_remove).props("color=negative outline")
            ui.button("Close", on_click=dialog.close).props("outline")

    dialog.open()


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/paths/my` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/paths/my")
    async def my_paths_page() -> None:
        if await require_user(store, api) is None:
            return

        render_shell(title="My Paths", store=store, api=api)
        selected: list[dict[str, Any]] = []
        details_by_path_id: dict[int, dict[str, Any]] = {}
        tracking_by_course_id: dict[int, dict[str, Any]] = {}
        loading = False

        with render_container():
            q = ui.input("Search").props("clearable debounce=300").classes("w-full")
            status_filter = ui.select(
                {"": "Any status", **{k: v for k, v in STATUS_OPTIONS}},
                label="Status",
                value="",
            )

            meta = ui.label("").classes("text-sm text-gray-600")

            @ui.refreshable
            def paths_list() -> None:
                needle = str(q.value or "").strip().lower()
                status_v = str(status_filter.value or "")
                shown = _filter_selected_paths(selected, needle=needle, status=status_v)

                with ui.column().classes("w-full gap-3"):
                    if loading:
                        render_card_skeletons(count=3)
                        return

                    if not shown:
                        ui.label("No selected paths.").classes("text-sm text-gray-600")
                        ui.button("Browse paths", on_click=lambda: ui.navigate.to("/paths")).props("outline")

                    for p in shown:
                        pid = int(p.get("id") or 0)
                        detail = details_by_path_id.get(pid) or {}
                        detail_courses = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
                        total_courses = len(detail_courses)
                        completed = 0
                        for c in detail_courses:
                            if not isinstance(c, dict):
                                continue
                            raw_cid = c.get("id")
                            if raw_cid is None:
                                continue
                            try:
                                cid = int(raw_cid)
                            except (TypeError, ValueError):
                                continue
                            if str((tracking_by_course_id.get(cid) or {}).get("status") or "") == "completed":
                                completed += 1
                        progress = (completed / total_courses) if total_courses else 0.0

                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(p.get("name") or "").classes("text-lg font-semibold")
                                    ui.label(p.get("description") or "").classes("text-sm text-gray-600")
                                    ui.label(status_label(str(p.get("status") or ""))).classes(
                                        status_chip_class(str(p.get("status") or ""))
                                    )
                                    if total_courses:
                                        ui.label(f"{completed}/{total_courses} completed").classes("text-sm text-gray-600")
                                        ui.linear_progress(progress, show_value=False).classes("w-full")

                                with ui.row().classes("items-center"):
                                    status_select = ui.select(
                                        options={k: v for k, v in STATUS_OPTIONS},
                                        value=str(p.get("status") or "interested"),
                                        label=None,
                                    ).props("dense")

                                    async def _on_status_change(e, _pid: int = pid, _select=status_select) -> None:
                                        _select.disable()
                                        try:
                                            options_map = {k: v for k, v in STATUS_OPTIONS}
                                            raw = e
                                            if not isinstance(e, (str, int, float, bool, dict)) and e is not None:
                                                raw = getattr(e, "value", None)
                                                if raw is None:
                                                    raw = getattr(e, "args", None)

                                            if isinstance(raw, dict):
                                                if raw.get("value") in options_map:
                                                    value = str(raw.get("value") or "")
                                                elif "label" in raw:
                                                    label = str(raw.get("label") or "").strip().lower()
                                                    value = ""
                                                    for key, opt_label in options_map.items():
                                                        if label and label == str(opt_label).strip().lower():
                                                            value = str(key)
                                                            break
                                                else:
                                                    value = ""
                                            else:
                                                value = str(raw or _select.value or "")

                                            if value:
                                                _select.value = value
                                                _select.update()
                                                await _set_status(_pid, value)
                                        finally:
                                            _select.enable()

                                    status_select.on("update:model-value", _on_status_change)

                                    async def _do_view(_pid: int = pid) -> None:
                                        await _open_details(_pid)

                                    ui.button(
                                        "View",
                                        on_click=_do_view,
                                    ).props("dense outline")

                                    async def _do_unselect(_pid: int = pid) -> None:
                                        await _unselect(_pid)

                                    ui.button(
                                        "Unselect",
                                        on_click=_do_unselect,
                                    ).props("dense color=negative outline")

            async def _load_selected() -> None:
                nonlocal selected, details_by_path_id, tracking_by_course_id, loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
                paths_list.refresh()
                try:
                    selected, details_by_path_id, tracking_by_course_id = await load_my_paths_page_data(api=api)
                    paths_list.refresh()
                    meta.text = f"{len(selected)} selected"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    selected = []
                    details_by_path_id = {}
                    tracking_by_course_id = {}
                    paths_list.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    refresh_btn.enable()
                    paths_list.refresh()

            @guard_ui_action(title="Unselect failed")
            async def _unselect(path_id: int) -> None:
                await api.post(f"/paths/{path_id}/unselect", {})
                await _load_selected()
                ui.notify("Removed from My Paths", type="positive")

            @guard_ui_action(title="Update status failed")
            async def _set_status(path_id: int, status: str) -> None:
                await api.post(f"/paths/{path_id}/status", {"status": status})
                await _load_selected()
                ui.notify("Status updated", type="positive")

            @guard_ui_action(title="Load path details failed")
            async def _open_details(path_id: int) -> None:
                detail = details_by_path_id.get(int(path_id)) or await api.get(f"/paths/{path_id}")

                row = next((p for p in selected if int(p.get("id") or 0) == int(path_id)), None) or {}
                courses_rows = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
                course_ids: list[int] = []
                for c in courses_rows:
                    if not isinstance(c, dict):
                        continue
                    try:
                        cid = int(c.get("id") or 0)
                    except (TypeError, ValueError):
                        continue
                    if cid > 0:
                        course_ids.append(cid)

                review_summary_by_course_id: dict[int, dict[str, Any]] = {}
                if course_ids:
                    try:
                        rows = await api.get("/courses/reviews/summary", params={"course_ids": course_ids})
                        for r in list(rows or []):
                            if not isinstance(r, dict):
                                continue
                            try:
                                cid = int(r.get("course_id") or 0)
                            except (TypeError, ValueError):
                                continue
                            if cid > 0:
                                review_summary_by_course_id[cid] = r
                    except ApiError:
                        review_summary_by_course_id = {}

                enriched_courses: list[dict[str, Any]] = []
                for c in courses_rows:
                    if not isinstance(c, dict):
                        continue
                    try:
                        cid = int(c.get("id") or 0)
                    except (TypeError, ValueError):
                        cid = 0
                    enriched = dict(c)
                    enriched["reviews"] = _format_review_summary(review_summary_by_course_id.get(cid))
                    enriched_courses.append(enriched)

                enriched_detail = dict(detail or {})
                enriched_detail["courses"] = enriched_courses
                _show_path_details_dialog(
                    detail=enriched_detail,
                    selected_row=dict(row),
                    on_update_status=lambda s: _set_status(int(path_id), s),
                    on_unselect=lambda: _unselect(int(path_id)),
                )

            q.on("update:model-value", lambda *_: paths_list.refresh())
            status_filter.on("update:model-value", lambda *_: paths_list.refresh())

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load_selected).props("outline")

            await _load_selected()
            paths_list()
