"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label, TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.courses_service import load_courses_and_tracking, load_tracking_map


def _parse_duration_hours(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/courses` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/courses")
    async def courses_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        render_shell(title="Courses", store=store, api=api)
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"

        with render_container():
            courses: list[dict[str, Any]] = []
            tracking_by_course_id: dict[int, dict[str, Any]] = {}

            with ui.row().classes("items-end w-full"):
                q = ui.input("Search").props("clearable debounce=300").classes("grow")
                provider = ui.input("Provider").props("clearable debounce=300")
                category = ui.input("Category").props("clearable debounce=300")
                status_filter = ui.select(
                    {"": "Any status", "not_tracked": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
                    label="My status",
                    value="",
                )

            with ui.expansion("More filters").props("dense"):
                with ui.row().classes("items-end w-full"):
                    level = ui.input("Level").props("clearable debounce=300")

            meta = ui.label("").classes("text-sm text-gray-600")
            loading = False

            async def _load() -> None:
                nonlocal courses, tracking_by_course_id, loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
                courses_list.refresh()
                try:
                    params: dict[str, Any] = {}
                    if q.value:
                        params["q"] = str(q.value)
                    if provider.value:
                        params["provider"] = str(provider.value)
                    if category.value:
                        params["category"] = str(category.value)
                    if level.value:
                        params["level"] = str(level.value)

                    courses, tracking_by_course_id = await load_courses_and_tracking(api=api, course_params=params or None)
                    courses_list.refresh()
                    meta.text = f"{len(courses)} courses"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    courses = []
                    tracking_by_course_id = {}
                    courses_list.refresh()
                    meta.text = "0 courses"
                finally:
                    loading = False
                    refresh_btn.enable()
                    courses_list.refresh()

            async def _reload_tracking_only() -> None:
                nonlocal tracking_by_course_id
                try:
                    tracking_by_course_id = await load_tracking_map(api=api)
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    tracking_by_course_id = {}
                    courses_list.refresh()
                    return
                courses_list.refresh()

            @guard_ui_action(title="Update status failed")
            async def _set_tracking(course_id: int, status: str) -> None:
                await api.post("/tracking", {"course_id": course_id, "status": status})
                await _reload_tracking_only()
                ui.notify("Updated status", type="positive")

            @guard_ui_action(title="Remove status failed")
            async def _clear_tracking(course_id: int) -> None:
                await api.post("/tracking/delete", {"course_id": course_id})
                await _reload_tracking_only()
                ui.notify("Removed status", type="positive")

            def _render_create_course_dialog() -> None:
                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
                    ui.label("Create Course").classes("text-xl font-semibold")

                    title = ui.input("Title").props("clearable").classes("w-full")
                    description = ui.textarea("Description").props("autogrow").classes("w-full")
                    provider_new = ui.input("Provider").props("clearable").classes("w-full")
                    category_new = ui.input("Category").props("clearable").classes("w-full")
                    level_new = ui.input("Level").props("clearable").classes("w-full")
                    duration_hours = ui.input("Duration hours").props("clearable").classes("w-full")
                    url = ui.input("URL").props("clearable").classes("w-full")

                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Create course failed")
                        async def _create() -> None:
                            dh_raw = str(duration_hours.value or "")
                            dh = _parse_duration_hours(dh_raw)
                            if dh_raw.strip() and dh is None:
                                ui.notify("Duration hours must be a number", type="negative")
                                return
                            if not str(description.value or "").strip():
                                ui.notify("Description is required", type="negative")
                                return

                            payload = {
                                "title": str(title.value or ""),
                                "description": str(description.value or "").strip(),
                                "provider": str(provider_new.value or ""),
                                "category": str(category_new.value or ""),
                                "level": str(level_new.value or ""),
                                "duration_hours": dh,
                                "url": str(url.value or ""),
                            }
                            await api.post("/courses", payload)
                            ui.notify("Course created", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Create", on_click=_create)
                        ui.button("Cancel", on_click=dialog.close).props("outline")

                dialog.open()

            def _render_edit_course_dialog(course: dict[str, Any]) -> None:
                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
                    ui.label("Edit Course").classes("text-xl font-semibold")

                    course_id = int(course.get("id") or 0)
                    title = ui.input("Title", value=str(course.get("title") or "")).props("clearable").classes("w-full")
                    description = (
                        ui.textarea("Description", value=str(course.get("description") or ""))
                        .props("autogrow")
                        .classes("w-full")
                    )
                    provider_new = (
                        ui.input("Provider", value=str(course.get("provider") or "")).props("clearable").classes("w-full")
                    )
                    category_new = (
                        ui.input("Category", value=str(course.get("category") or "")).props("clearable").classes("w-full")
                    )
                    level_new = ui.input("Level", value=str(course.get("level") or "")).props("clearable").classes("w-full")
                    duration_hours = (
                        ui.input("Duration hours", value=str(course.get("duration_hours") or ""))
                        .props("clearable")
                        .classes("w-full")
                    )
                    url = ui.input("URL", value=str(course.get("url") or "")).props("clearable").classes("w-full")

                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Save changes failed")
                        async def _save() -> None:
                            dh_raw = str(duration_hours.value or "")
                            dh = _parse_duration_hours(dh_raw)
                            if dh_raw.strip() and dh is None:
                                ui.notify("Duration hours must be a number", type="negative")
                                return
                            if not str(description.value or "").strip():
                                ui.notify("Description is required", type="negative")
                                return

                            payload = {
                                "title": str(title.value or ""),
                                "description": str(description.value or "").strip(),
                                "provider": str(provider_new.value or ""),
                                "category": str(category_new.value or ""),
                                "level": str(level_new.value or ""),
                                "duration_hours": dh,
                                "url": str(url.value or ""),
                            }
                            await api.put(f"/courses/{course_id}", payload)
                            ui.notify("Course updated", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Save", on_click=_save)
                        ui.button("Cancel", on_click=dialog.close).props("outline")

                dialog.open()

            async def _confirm_delete_course(course_id: int) -> None:
                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog"):
                    ui.label("Delete this course?").classes("text-lg font-semibold")
                    ui.label("This cannot be undone.").classes("text-sm text-gray-600")
                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Delete course failed")
                        async def _delete() -> None:
                            await api.delete(f"/courses/{course_id}")
                            ui.notify("Course deleted", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Delete", on_click=_delete).props("color=negative")
                        ui.button("Cancel", on_click=dialog.close).props("outline")
                dialog.open()

            @guard_ui_action(title="Load course details failed")
            async def _open_details(course_id: int) -> None:
                course = await api.get(f"/courses/{course_id}")

                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
                    ui.label(course.get("title") or "").classes("text-xl font-semibold")
                    if str(course.get("description") or "").strip():
                        ui.label(str(course.get("description") or "")).classes("text-sm text-gray-600")
                    ui.label(
                        f"{course.get('provider') or ''} · {course.get('category') or ''} · {course.get('level') or ''}"
                    ).classes("text-sm text-gray-600")

                    if course.get("duration_hours") is not None:
                        ui.label(f"Duration: {course.get('duration_hours')}h").classes("text-sm")

                    if course.get("url"):
                        ui.link("Open link", str(course.get("url"))).props("target=_blank").classes("text-sm")

                    tracked = tracking_by_course_id.get(int(course_id))
                    ui.separator()
                    ui.label("My status").classes("text-lg font-semibold")

                    status_select = ui.select(
                        options={k: v for k, v in TRACKING_STATUS_OPTIONS},
                        value=str((tracked or {}).get("status") or "interested"),
                        label="Status",
                    )

                    with ui.row().classes("justify-end mt-4"):

                        async def _save_status() -> None:
                            await _set_tracking(int(course_id), str(status_select.value or ""))

                        ui.button("Update", on_click=_save_status).props("outline")
                        if tracked:

                            async def _do_clear() -> None:
                                await _clear_tracking(int(course_id))

                            ui.button("Clear", on_click=_do_clear).props("color=negative outline")
                        ui.button("Close", on_click=dialog.close).props("outline")

                    can_edit = is_admin or (str(course.get("created_by") or "") == username)
                    if can_edit:
                        ui.separator()
                        with ui.row().classes("justify-end"):
                            ui.button("Edit", on_click=lambda c=course: _render_edit_course_dialog(c)).props("outline")

                            async def _do_delete() -> None:
                                await _confirm_delete_course(int(course_id))

                            ui.button("Delete", on_click=_do_delete).props("color=negative outline")

                dialog.open()

            @ui.refreshable
            def courses_list() -> None:
                needle = str(q.value or "").strip().lower()
                provider_v = str(provider.value or "").strip().lower()
                category_v = str(category.value or "").strip().lower()
                level_v = str(level.value or "").strip().lower()
                status_v = str(status_filter.value or "")

                shown = courses
                if needle:
                    shown = [c for c in shown if needle in str(c.get("title") or "").lower()]
                if provider_v:
                    shown = [c for c in shown if provider_v in str(c.get("provider") or "").lower()]
                if category_v:
                    shown = [c for c in shown if category_v in str(c.get("category") or "").lower()]
                if level_v:
                    shown = [c for c in shown if level_v in str(c.get("level") or "").lower()]

                if status_v:
                    if status_v == "not_tracked":
                        shown = [c for c in shown if int(c.get("id") or 0) not in tracking_by_course_id]
                    else:
                        shown = [
                            c
                            for c in shown
                            if str((tracking_by_course_id.get(int(c.get("id") or 0)) or {}).get("status") or "") == status_v
                        ]

                with ui.column().classes("w-full gap-3"):
                    if loading:
                        render_card_skeletons(count=4)
                        return

                    if not shown:
                        ui.label("No courses match your filters.").classes("text-sm text-gray-600")
                        with ui.row().classes("items-center gap-2"):
                            ui.button("Clear filters", on_click=lambda: _clear_filters()).props("outline")
                            ui.button("Refresh", on_click=_load).props("outline")

                    for c in shown:
                        course_id = int(c.get("id") or 0)
                        tracked = tracking_by_course_id.get(course_id)
                        can_edit = is_admin or (str(c.get("created_by") or "") == username)
                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(c.get("title") or "").classes("text-lg font-semibold")
                                    if str(c.get("description") or "").strip():
                                        ui.label(str(c.get("description") or "")).classes("text-sm text-gray-600")
                                    with ui.row().classes("items-center gap-2 flex-wrap"):
                                        if str(c.get("provider") or "").strip():
                                            ui.label(str(c.get("provider") or "")).classes("lp-meta-chip")
                                        if str(c.get("category") or "").strip():
                                            ui.label(str(c.get("category") or "")).classes("lp-meta-chip")
                                        if str(c.get("level") or "").strip():
                                            ui.label(str(c.get("level") or "")).classes("lp-meta-chip")
                                    ui.label(tracking_label((tracked or {}).get("status"))).classes(
                                        tracking_chip_class((tracked or {}).get("status"))
                                    )

                                with ui.row().classes("items-center"):

                                    async def _view(_cid: int = course_id) -> None:
                                        await _open_details(_cid)

                                    ui.button("View", on_click=_view).props("outline")

                                    current_status = str((tracked or {}).get("status") or "")
                                    status_select = ui.select(
                                        options={"": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
                                        value=current_status,
                                        label=None,
                                    ).props("dense")

                                    async def _on_status_change(e, _cid: int = course_id) -> None:
                                        value = str(getattr(e, "value", "") or "")
                                        if not value:
                                            if int(_cid) in tracking_by_course_id:
                                                await _clear_tracking(_cid)
                                            return
                                        await _set_tracking(_cid, value)

                                    status_select.on("update:model-value", _on_status_change)

                            if can_edit:
                                with ui.row().classes("justify-end mt-2"):
                                    ui.button("Edit", on_click=lambda course=c: _render_edit_course_dialog(course)).props(
                                        "dense outline"
                                    )

                                    async def _do_delete(_cid: int = course_id) -> None:
                                        await _confirm_delete_course(_cid)

                                    ui.button("Delete", on_click=_do_delete).props("dense color=negative outline")

            def _refresh_list(*_: Any) -> None:
                courses_list.refresh()

            def _clear_filters() -> None:
                q.value = ""
                provider.value = ""
                category.value = ""
                level.value = ""
                status_filter.value = ""
                courses_list.refresh()

            q.on("update:model-value", _refresh_list)
            provider.on("update:model-value", _refresh_list)
            category.on("update:model-value", _refresh_list)
            level.on("update:model-value", _refresh_list)
            status_filter.on("update:model-value", _refresh_list)

            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-2"):
                    refresh_btn = ui.button("Refresh", on_click=_load).props("outline")
                    ui.button("New course", on_click=_render_create_course_dialog)

            await _load()
            courses_list()
