"""My Paths page for the NiceGUI frontend."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.paths import _status_chip_class, _status_label, STATUS_OPTIONS


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


async def _load_selected_paths(api: ApiClient) -> list[dict[str, Any]]:
    """Load the current user's selected paths."""
    return list(await api.get("/paths/selected/list") or [])


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

        ui.label(f"Status: {_status_label(str(selected_row.get('status') or ''))}").classes("text-sm")

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
            ],
            rows=courses_rows,
        ).classes("w-full")

        with ui.row().classes("justify-end mt-4"):

            async def _update() -> None:
                await on_update_status(str(status_select.value or ""))

            ui.button("Update status", on_click=_update).props("outline")

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
        loading = False

        with render_container():
            q = ui.input("Search").props("clearable").classes("w-full")
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
                    if not shown:
                        ui.label("No selected paths.").classes("text-sm text-gray-600")

                    for p in shown:
                        pid = int(p.get("id") or 0)
                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(p.get("name") or "").classes("text-lg font-semibold")
                                    ui.label(p.get("description") or "").classes("text-sm text-gray-600")
                                    ui.label(_status_label(str(p.get("status") or ""))).classes(
                                        _status_chip_class(str(p.get("status") or ""))
                                    )

                                with ui.row().classes("items-center"):
                                    status_select = ui.select(
                                        options={k: v for k, v in STATUS_OPTIONS},
                                        value=str(p.get("status") or "interested"),
                                        label=None,
                                    ).props("dense")

                                    async def _do_set(_pid: int = pid, _sel=status_select) -> None:
                                        await _set_status(_pid, str(_sel.value or ""))

                                    ui.button(
                                        "Set",
                                        on_click=_do_set,
                                    ).props("dense outline")

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
                nonlocal selected, loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."
                try:
                    selected = await _load_selected_paths(api)
                    paths_list.refresh()
                    meta.text = f"{len(selected)} selected"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    selected = []
                    paths_list.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    refresh_btn.enable()

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
                detail = await api.get(f"/paths/{path_id}")

                row = next((p for p in selected if int(p.get("id") or 0) == int(path_id)), None) or {}
                _show_path_details_dialog(
                    detail=dict(detail or {}),
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
