"""My Courses page for the NiceGUI frontend.

This page focuses on the current user's tracking list and status updates.
"""

from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.courses import _tracking_label, TRACKING_STATUS_OPTIONS


def _build_tracked_items(
    *,
    courses_by_id: dict[int, dict[str, Any]],
    tracking_by_id: dict[int, dict[str, Any]],
    needle: str,
    status: str,
) -> list[tuple[int, dict[str, Any], dict[str, Any]]]:
    """Build and filter the tracked course list for rendering.

    Args:
        courses_by_id: Course lookup by course id.
        tracking_by_id: Tracking lookup by course id.
        needle: Lower-cased substring to match against the course title.
        status: Optional status filter (empty string means "any").

    Returns:
        A list of `(course_id, course_payload, tracking_payload)` tuples.
    """
    items: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for course_id, tr in tracking_by_id.items():
        course = courses_by_id.get(course_id) or {"id": course_id, "title": f"Course #{course_id}"}
        items.append((course_id, course, tr))

    if needle:
        items = [(cid, c, tr) for cid, c, tr in items if needle in str(c.get("title") or "").lower()]
    if status:
        items = [(cid, c, tr) for cid, c, tr in items if str(tr.get("status") or "") == status]

    return items


async def _load_courses_and_tracking(api: ApiClient) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """Load all courses and the current user's tracking map.

    Args:
        api: API client.

    Returns:
        Tuple of `(courses_by_id, tracking_by_id)`.

    Raises:
        ApiError: If the backend requests fail.
    """
    courses_result, tracking_result = await asyncio.gather(api.get("/courses"), api.get("/tracking"))

    courses_by_id: dict[int, dict[str, Any]] = {}
    for c in list(courses_result or []):
        if isinstance(c, dict) and "id" in c:
            courses_by_id[int(c["id"])] = c

    tracking_by_id: dict[int, dict[str, Any]] = {}
    for r in list(tracking_result or []):
        if not isinstance(r, dict):
            continue
        raw = str(r.get("course_id") or "")
        if not raw.isdigit():
            continue
        tracking_by_id[int(raw)] = r

    return courses_by_id, tracking_by_id


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/courses/my` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/courses/my")
    async def my_courses_page() -> None:
        if await require_user(store, api) is None:
            return

        render_shell(title="My Courses", store=store, api=api)
        courses_by_id: dict[int, dict[str, Any]] = {}
        tracking_by_id: dict[int, dict[str, Any]] = {}
        loading = False

        async def _load() -> None:
            """Fetch the latest data and refresh the rendered list."""
            nonlocal courses_by_id, tracking_by_id, loading
            if loading:
                return
            loading = True
            refresh_btn.disable()
            meta.text = "Loading..."
            try:
                courses_by_id, tracking_by_id = await _load_courses_and_tracking(api)
                courses_list.refresh()
                meta.text = f"{len(tracking_by_id)} tracked"
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                courses_by_id = {}
                tracking_by_id = {}
                courses_list.refresh()
                meta.text = "Failed to load"
            finally:
                loading = False
                refresh_btn.enable()

        @guard_ui_action(title="Update status failed")
        async def _set_status(course_id: int, status: str) -> None:
            await api.post("/tracking", {"course_id": course_id, "status": status})
            await _load()
            ui.notify("Status updated", type="positive")

        @guard_ui_action(title="Remove status failed")
        async def _clear(course_id: int) -> None:
            await api.post("/tracking/delete", {"course_id": course_id})
            await _load()
            ui.notify("Removed status", type="positive")

        @guard_ui_action(title="Load course details failed")
        async def _open_details(course_id: int) -> None:
            course = await api.get(f"/courses/{course_id}")

            tracked = tracking_by_id.get(int(course_id))

            with ui.dialog() as dialog, ui.card().classes("w-[min(800px,95vw)]"):
                ui.label(course.get("title") or "").classes("text-xl font-semibold")
                ui.label(
                    f"{course.get('provider') or ''} · {course.get('category') or ''} · {course.get('level') or ''}"
                ).classes("text-sm text-gray-600")
                if course.get("duration_hours") is not None:
                    ui.label(f"Duration: {course.get('duration_hours')}h").classes("text-sm")
                if course.get("url"):
                    ui.link("Open link", str(course.get("url"))).props("target=_blank").classes("text-sm")

                ui.separator()
                ui.label("My status").classes("text-lg font-semibold")
                status_select = ui.select(
                    options={k: v for k, v in TRACKING_STATUS_OPTIONS},
                    value=str((tracked or {}).get("status") or "interested"),
                    label="Status",
                )

                with ui.row().classes("justify-end mt-4"):

                    async def _save() -> None:
                        await _set_status(int(course_id), str(status_select.value or ""))

                    ui.button("Update", on_click=_save).props("outline")
                    if tracked:

                        async def _do_clear() -> None:
                            await _clear(int(course_id))

                        ui.button("Clear", on_click=_do_clear).props("color=negative outline")
                    ui.button("Close", on_click=dialog.close).props("outline")

            dialog.open()

        def _refresh(*_: Any) -> None:
            courses_list.refresh()

        with render_container():
            q = ui.input("Search").props("clearable").classes("w-full")
            status_filter = ui.select(
                {"": "Any status", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
                label="Status",
                value="",
            )

            meta = ui.label("").classes("text-sm text-gray-600")

            @ui.refreshable
            def courses_list() -> None:
                needle = str(q.value or "").strip().lower()
                status_v = str(status_filter.value or "")
                tracked_items = _build_tracked_items(
                    courses_by_id=courses_by_id,
                    tracking_by_id=tracking_by_id,
                    needle=needle,
                    status=status_v,
                )

                with ui.column().classes("w-full gap-3"):
                    if not tracked_items:
                        ui.label("No tracked courses yet.").classes("text-sm text-gray-600")

                    for cid, course, tr in tracked_items:
                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(course.get("title") or "").classes("text-lg font-semibold")
                                    ui.label(f"Status: {_tracking_label(str(tr.get('status') or ''))}").classes("text-sm")

                                with ui.row().classes("items-center"):
                                    status_select = ui.select(
                                        options={k: v for k, v in TRACKING_STATUS_OPTIONS},
                                        value=str(tr.get("status") or "interested"),
                                        label=None,
                                    ).props("dense")

                                    async def _quick_set(_cid: int = cid, _sel=status_select) -> None:
                                        await _set_status(_cid, str(_sel.value or ""))

                                    ui.button("Set", on_click=_quick_set).props("dense outline")

                                    async def _view(_cid: int = cid) -> None:
                                        await _open_details(_cid)

                                    ui.button("View", on_click=_view).props("dense outline")

                                    async def _remove(_cid: int = cid) -> None:
                                        await _clear(_cid)

                                    ui.button("Clear", on_click=_remove).props("dense color=negative outline")

            q.on("update:model-value", _refresh)
            status_filter.on("update:model-value", _refresh)

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load).props("outline")

            await _load()
            courses_list()
