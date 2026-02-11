"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


TRACKING_STATUS_OPTIONS: list[tuple[str, str]] = [
    ("interested", "Interested"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
]


def _tracking_label(value: str | None) -> str:
    v = (value or "").strip()
    for key, label in TRACKING_STATUS_OPTIONS:
        if v == key:
            return label
    return "Not tracked"


def _tracking_chip_class(value: str | None) -> str:
    v = (value or "").strip()
    if not v:
        return "lp-chip lp-chip--muted"
    if v == "interested":
        return "lp-chip lp-chip--sky"
    if v == "in_progress":
        return "lp-chip lp-chip--teal"
    if v == "completed":
        return "lp-chip lp-chip--lime"
    return "lp-chip"


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
        is_admin = str(user.get("role") or "") == "admin"

        with render_container():
            courses: list[dict[str, Any]] = []
            tracking_by_course_id: dict[int, dict[str, Any]] = {}

            with ui.row().classes("items-end w-full"):
                q = ui.input("Search").props("clearable").classes("grow")
                provider = ui.input("Provider").props("clearable")
                category = ui.input("Category").props("clearable")
                level = ui.input("Level").props("clearable")
                status_filter = ui.select(
                    {"": "Any status", "not_tracked": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
                    label="My status",
                    value="",
                )

            meta = ui.label("").classes("text-sm text-gray-600")
            loading = False

            async def _load() -> None:
                nonlocal courses, tracking_by_course_id, loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
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

                    courses_result, tracking_result = await asyncio.gather(
                        api.get("/courses", params=params or None),
                        api.get("/tracking"),
                    )
                    courses = list(courses_result or [])
                    tracking_rows = list(tracking_result or [])
                    tracking_by_course_id = {
                        int(r["course_id"]): r
                        for r in tracking_rows
                        if isinstance(r, dict) and str(r.get("course_id") or "").isdigit()
                    }
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

            async def _reload_tracking_only() -> None:
                nonlocal tracking_by_course_id
                try:
                    tracking_result = await api.get("/tracking")
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    tracking_by_course_id = {}
                    courses_list.refresh()
                    return
                tracking_rows = list(tracking_result or [])
                tracking_by_course_id = {
                    int(r["course_id"]): r
                    for r in tracking_rows
                    if isinstance(r, dict) and str(r.get("course_id") or "").isdigit()
                }
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
                with ui.dialog() as dialog, ui.card().classes("w-[min(700px,95vw)]"):
                    ui.label("Create Course").classes("text-xl font-semibold")

                    title = ui.input("Title").props("clearable").classes("w-full")
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

                            payload = {
                                "title": str(title.value or ""),
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
                with ui.dialog() as dialog, ui.card().classes("w-[min(700px,95vw)]"):
                    ui.label("Edit Course").classes("text-xl font-semibold")

                    course_id = int(course.get("id") or 0)
                    title = ui.input("Title", value=str(course.get("title") or "")).props("clearable").classes("w-full")
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

                            payload = {
                                "title": str(title.value or ""),
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
                with ui.dialog() as dialog, ui.card():
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

                with ui.dialog() as dialog, ui.card().classes("w-[min(800px,95vw)]"):
                    ui.label(course.get("title") or "").classes("text-xl font-semibold")
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

                    if is_admin:
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
                    if not shown:
                        ui.label("No courses match your filters.").classes("text-sm text-gray-600")

                    for c in shown:
                        course_id = int(c.get("id") or 0)
                        tracked = tracking_by_course_id.get(course_id)
                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(c.get("title") or "").classes("text-lg font-semibold")
                                    meta_bits = [
                                        str(c.get("provider") or "").strip(),
                                        str(c.get("category") or "").strip(),
                                        str(c.get("level") or "").strip(),
                                    ]
                                    ui.label(" · ".join([b for b in meta_bits if b])).classes("text-sm text-gray-600")
                                    ui.label(_tracking_label((tracked or {}).get("status"))).classes(
                                        _tracking_chip_class((tracked or {}).get("status"))
                                    )

                                with ui.row().classes("items-center"):

                                    async def _view(_cid: int = course_id) -> None:
                                        await _open_details(_cid)

                                    ui.button("View", on_click=_view).props("outline")

                                    if tracked:
                                        status_select = ui.select(
                                            options={k: v for k, v in TRACKING_STATUS_OPTIONS},
                                            value=str(tracked.get("status") or "interested"),
                                            label=None,
                                        ).props("dense")

                                        async def _quick_set(_cid: int = course_id, _sel=status_select) -> None:
                                            await _set_tracking(_cid, str(_sel.value or ""))

                                        ui.button("Set", on_click=_quick_set).props("dense outline")

                                        async def _quick_clear(_cid: int = course_id) -> None:
                                            await _clear_tracking(_cid)

                                        ui.button("Clear", on_click=_quick_clear).props("dense color=negative outline")
                                    else:
                                        status_select = ui.select(
                                            options={k: v for k, v in TRACKING_STATUS_OPTIONS},
                                            value="interested",
                                            label=None,
                                        ).props("dense")

                                        async def _quick_track(_cid: int = course_id, _sel=status_select) -> None:
                                            await _set_tracking(_cid, str(_sel.value or ""))

                                        ui.button("Track", on_click=_quick_track).props("dense")

                            if is_admin:
                                with ui.row().classes("justify-end mt-2"):
                                    ui.button("Edit", on_click=lambda course=c: _render_edit_course_dialog(course)).props(
                                        "dense outline"
                                    )

                                    async def _do_delete(_cid: int = course_id) -> None:
                                        await _confirm_delete_course(_cid)

                                    ui.button("Delete", on_click=_do_delete).props("dense color=negative outline")

            def _refresh_list(*_: Any) -> None:
                courses_list.refresh()

            q.on("update:model-value", _refresh_list)
            provider.on("update:model-value", _refresh_list)
            category.on("update:model-value", _refresh_list)
            level.on("update:model-value", _refresh_list)
            status_filter.on("update:model-value", _refresh_list)

            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-2"):
                    refresh_btn = ui.button("Refresh", on_click=lambda: asyncio.create_task(_load())).props("outline")
                    if is_admin:
                        ui.button("New course", on_click=_render_create_course_dialog)

            await _load()
            courses_list()
