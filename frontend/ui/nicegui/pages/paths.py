"""Paths browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import status_chip_class, status_label, STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.paths_service import (
    index_courses_by_int_id,
    index_rows_by_int_id,
    load_paths_page_data,
)


_index_rows_by_int_id = index_rows_by_int_id
_index_courses_by_int_id = index_courses_by_int_id


def _course_options(courses: list[dict[str, Any]] | None) -> dict[int, str]:
    """Convert courses into select options."""
    options: dict[int, str] = {}
    for c in list(courses or []):
        if not isinstance(c, dict) or c.get("id") is None:
            continue
        try:
            cid = int(c["id"])
        except (TypeError, ValueError):
            continue
        options[cid] = f"{c.get('title') or ''} (#{cid})"
    return options


def _filter_paths(paths: list[dict[str, Any]] | None, needle: str) -> list[dict[str, Any]]:
    """Filter paths by a lower-cased substring match on name."""
    if not needle:
        return list(paths or [])
    return [p for p in list(paths or []) if needle in str(p.get("name") or "").lower()]


async def _load_paths_page_data(
    api: ApiClient,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    """Compat shim: use the NiceGUI paths service layer."""
    return await load_paths_page_data(api=api)


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/paths` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/paths")
    async def paths_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Paths", store=store, api=api)
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"

        paths: list[dict[str, Any]] = []
        selected_by_id: dict[int, dict[str, Any]] = {}
        courses: list[dict[str, Any]] = []
        course_by_id: dict[int, dict[str, Any]] = {}
        loading = False

        async def _reload_selected() -> None:
            """Reload selected path rows (used after select/unselect/status updates)."""
            nonlocal selected_by_id
            try:
                selected_result = await api.get("/paths/selected/list")
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                selected_by_id = {}
                return
            selected_by_id = _index_rows_by_int_id(list(selected_result or []))

        @guard_ui_action(title="Select failed")
        async def _select(path_id: int) -> None:
            await api.post(f"/paths/{path_id}/select", {})
            await _reload_selected()
            paths_list.refresh()

        @guard_ui_action(title="Unselect failed")
        async def _unselect(path_id: int) -> None:
            await api.post(f"/paths/{path_id}/unselect", {})
            await _reload_selected()
            paths_list.refresh()

        @guard_ui_action(title="Update status failed")
        async def _set_status(path_id: int, status: str) -> None:
            await api.post(f"/paths/{path_id}/status", {"status": status})
            await _reload_selected()
            paths_list.refresh()

        @guard_ui_action(title="Delete path failed")
        async def _delete_path(path_id: int) -> None:
            await api.delete(f"/paths/{path_id}")
            await _load_all()
            ui.notify("Path deleted", type="positive")

        async def _open_edit(*, path_id: int, detail: dict[str, Any], detail_dialog: ui.dialog) -> None:
            """Open an edit dialog for a path (owner/admin only, enforced by backend)."""
            ordered_course_ids: list[int] = [
                int(c.get("id")) for c in (detail.get("courses") or []) if isinstance(c, dict) and c.get("id") is not None
            ]

            with ui.dialog() as edit_dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
                ui.label("Edit Path").classes("text-xl font-semibold")

                name = ui.input("Name", value=str(detail.get("name") or "")).props("clearable").classes("w-full")
                description = (
                    ui.textarea("Description", value=str(detail.get("description") or "")).props("autogrow").classes("w-full")
                )

                ui.separator()
                ui.label("Course Order").classes("text-lg font-semibold")

                add_course = ui.select(
                    {cid: f"{c.get('title') or ''} (#{cid})" for cid, c in sorted(course_by_id.items())},
                    label="Add course",
                ).classes("w-full")

                async def _add_course() -> None:
                    try:
                        cid = int(add_course.value)
                    except (TypeError, ValueError):
                        return
                    if cid not in ordered_course_ids:
                        ordered_course_ids.append(cid)
                        courses_list.refresh()

                ui.button("Add", on_click=_add_course).props("outline")

                @ui.refreshable
                def courses_list() -> None:
                    with ui.column().classes("w-full gap-2"):
                        if not ordered_course_ids:
                            ui.label("No courses selected.").classes("text-sm text-gray-600")
                        for idx, cid in enumerate(list(ordered_course_ids)):
                            c = course_by_id.get(cid) or {}
                            title = str(c.get("title") or f"Course #{cid}")
                            with ui.row().classes("items-center justify-between"):
                                ui.label(f"{idx + 1}. {title}").classes("text-sm")
                                with ui.row().classes("items-center"):

                                    def _move_up(_idx: int = idx) -> None:
                                        if _idx <= 0:
                                            return
                                        ordered_course_ids[_idx - 1], ordered_course_ids[_idx] = (
                                            ordered_course_ids[_idx],
                                            ordered_course_ids[_idx - 1],
                                        )
                                        courses_list.refresh()

                                    def _move_down(_idx: int = idx) -> None:
                                        if _idx >= len(ordered_course_ids) - 1:
                                            return
                                        ordered_course_ids[_idx + 1], ordered_course_ids[_idx] = (
                                            ordered_course_ids[_idx],
                                            ordered_course_ids[_idx + 1],
                                        )
                                        courses_list.refresh()

                                    def _remove(_cid: int = cid) -> None:
                                        if _cid in ordered_course_ids:
                                            ordered_course_ids.remove(_cid)
                                            courses_list.refresh()

                                    ui.button("Up", on_click=_move_up).props("dense outline")
                                    ui.button("Down", on_click=_move_down).props("dense outline")
                                    ui.button("Remove", on_click=_remove).props("dense color=negative outline")

                courses_list()

                with ui.row().classes("justify-end mt-4"):

                    @guard_ui_action(title="Save changes failed")
                    async def _save() -> None:
                        payload = {
                            "name": str(name.value or ""),
                            "description": str(description.value or ""),
                            "course_ids": ordered_course_ids,
                        }
                        await api.put(f"/paths/{path_id}", payload)
                        await _load_all()
                        paths_list.refresh()
                        ui.notify("Path updated", type="positive")
                        edit_dialog.close()
                        detail_dialog.close()

                    ui.button("Save", on_click=_save)
                    ui.button("Cancel", on_click=edit_dialog.close).props("outline")

            edit_dialog.open()

        @guard_ui_action(title="Load path details failed")
        async def _open_details(path_id: int) -> None:
            """Open a detail dialog for a path."""
            detail = await api.get(f"/paths/{path_id}")

            with ui.dialog() as dialog, ui.card().classes("w-[min(900px,95vw)]"):
                ui.label(detail.get("name") or "").classes("text-xl font-semibold")
                ui.label(detail.get("description") or "").classes("text-sm text-gray-600")

                selected = selected_by_id.get(int(path_id))
                with ui.row().classes("items-center"):
                    ui.label(f"Status: {status_label((selected or {}).get('status'))}").classes("text-sm")

                    if selected:
                        status_select = ui.select(
                            options={k: v for k, v in STATUS_OPTIONS},
                            value=str(selected.get("status") or "interested"),
                        ).props("dense")

                        async def _update_status() -> None:
                            await _set_status(path_id, str(status_select.value or ""))

                        ui.button("Update status", on_click=_update_status).props("outline")

                courses_rows = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
                ui.label("Courses").classes("text-lg font-semibold mt-4")
                ui.table(
                    columns=[
                        {"name": "id", "label": "ID", "field": "id"},
                        {"name": "title", "label": "Title", "field": "title"},
                        {"name": "provider", "label": "Provider", "field": "provider"},
                        {"name": "category", "label": "Category", "field": "category"},
                        {"name": "level", "label": "Level", "field": "level"},
                    ],
                    rows=courses_rows,
                ).classes("w-full")

                with ui.row().classes("justify-end mt-4"):
                    can_edit = is_admin or (str(detail.get("created_by") or "") == username)
                    if can_edit:

                        async def _edit() -> None:
                            await _open_edit(path_id=int(path_id), detail=detail, detail_dialog=dialog)

                        ui.button("Edit", on_click=_edit).props("outline")

                        @guard_ui_action(title="Delete path failed")
                        async def _delete() -> None:
                            await api.delete(f"/paths/{path_id}")
                            await _load_all()
                            paths_list.refresh()
                            dialog.close()

                        ui.button("Delete", on_click=_delete).props("color=negative outline")
                    ui.button("Close", on_click=dialog.close).props("outline")

            dialog.open()

        def _refresh_list(*_: Any) -> None:
            paths_list.refresh()

        with render_container():
            q = ui.input("Search").props("clearable debounce=300").classes("w-full")
            meta = ui.label("").classes("text-sm text-gray-600")

            @ui.refreshable
            def paths_list() -> None:
                needle = str(q.value or "").strip().lower()
                shown = _filter_paths(paths, needle)

                with ui.column().classes("w-full gap-3"):
                    if loading:
                        render_card_skeletons(count=4)
                        return

                    if not shown:
                        ui.label("No paths found.").classes("text-sm text-gray-600")
                        ui.button("Browse courses", on_click=lambda: ui.navigate.to("/courses")).props("outline")

                    for p in shown:
                        pid = int(p.get("id") or 0)
                        selected = selected_by_id.get(pid)
                        can_edit = is_admin or (str(p.get("created_by") or "") == username)

                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(p.get("name") or "").classes("text-lg font-semibold")
                                    ui.label(p.get("description") or "").classes("text-sm text-gray-600")
                                    ui.label(status_label((selected or {}).get("status"))).classes(
                                        status_chip_class((selected or {}).get("status"))
                                    )

                                with ui.row().classes("items-center"):

                                    async def _view(_pid: int = pid) -> None:
                                        await _open_details(_pid)

                                    ui.button("View", on_click=_view).props("outline")

                                    if selected:

                                        async def _do_unselect(_pid: int = pid) -> None:
                                            await _unselect(_pid)

                                        ui.button("Unselect", on_click=_do_unselect).props("outline")
                                    else:

                                        async def _do_select(_pid: int = pid) -> None:
                                            await _select(_pid)

                                        ui.button("Select", on_click=_do_select)

                                    if can_edit:

                                        async def _do_delete(_pid: int = pid) -> None:
                                            await _delete_path(_pid)

                                        ui.button("Delete", on_click=_do_delete).props("color=negative outline")

            q.on("update:model-value", _refresh_list)

            ui.separator()
            ui.label("Create Path").classes("text-lg font-semibold")

            name = ui.input("Name").props("clearable").classes("w-full")
            description = ui.textarea("Description").props("autogrow").classes("w-full")
            course_ids = ui.select({}, label="Courses (ordered)", multiple=True).classes("w-full")

            @guard_ui_action(title="Create path failed")
            async def _create() -> None:
                payload = {
                    "name": str(name.value or ""),
                    "description": str(description.value or ""),
                    "course_ids": list(course_ids.value or []),
                }
                await api.post("/paths", payload)
                name.value = ""
                description.value = ""
                course_ids.value = []
                await _load_all()
                ui.notify("Path created", type="positive")

            ui.button("Create path", on_click=_create)

            async def _load_all() -> None:
                """Reload all data for this page."""
                nonlocal paths, selected_by_id, courses, course_by_id, loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
                paths_list.refresh()
                try:
                    paths, selected_by_id, courses, course_by_id = await _load_paths_page_data(api)
                    course_ids.options = _course_options(courses)
                    course_ids.update()
                    paths_list.refresh()
                    meta.text = f"{len(paths)} paths"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    paths = []
                    selected_by_id = {}
                    courses = []
                    course_by_id = {}
                    paths_list.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    refresh_btn.enable()
                    paths_list.refresh()

            with ui.row().classes("items-center justify-between w-full mt-2"):
                refresh_btn = ui.button("Refresh", on_click=_load_all).props("outline")

            await _load_all()
            paths_list()
