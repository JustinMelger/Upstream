"""Dialog builders for the Paths page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.core.errors import guard_ui_action


def build_share_path_dialog(
    *,
    username: str,
    on_submit: Callable[[dict[str, Any]], Awaitable[None]],
) -> tuple[ui.dialog, Any, Callable[[], None]]:
    """Build the share-path dialog and return open helper + course select handle."""
    path_draft_key = f"paths_share_draft::{username}"
    create_dialog = ui.dialog()
    with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label("Share Path").classes("text-xl font-semibold")
        ui.label("Save a draft if you want feedback before publishing.").classes("text-xs").style("color: var(--lp-muted)")
        create_name = ui.input("Name").props("clearable").classes("w-full")
        create_description = ui.textarea("Description").props("autogrow").classes("w-full")
        create_course_ids = ui.select({}, label="Courses (ordered)", multiple=True).classes("w-full")

        def _path_draft_payload() -> dict[str, Any]:
            return {
                "name": str(create_name.value or ""),
                "description": str(create_description.value or ""),
                "course_ids": list(create_course_ids.value or []),
            }

        def _apply_path_draft(raw: Any) -> None:
            draft = raw if isinstance(raw, dict) else {}
            create_name.value = str(draft.get("name") or "")
            create_description.value = str(draft.get("description") or "")
            create_course_ids.value = list(draft.get("course_ids") or [])
            create_course_ids.update()

        with ui.row().classes("justify-end mt-4"):

            def _save_draft() -> None:
                app.storage.user[path_draft_key] = _path_draft_payload()
                ui.notify("Draft saved", type="positive")

            def _load_draft() -> None:
                draft = app.storage.user.get(path_draft_key)
                if not isinstance(draft, dict):
                    ui.notify("No saved draft found", type="warning")
                    return
                _apply_path_draft(draft)
                ui.notify("Draft loaded", type="positive")

            @guard_ui_action(title="Share path failed")
            async def _create_submit() -> None:
                payload = {
                    "name": str(create_name.value or ""),
                    "description": str(create_description.value or ""),
                    "course_ids": list(create_course_ids.value or []),
                }
                await on_submit(payload)
                app.storage.user.pop(path_draft_key, None)
                ui.notify("Path shared", type="positive")
                create_dialog.close()

            ui.button("Save draft", on_click=_save_draft).props("outline")
            ui.button("Load draft", on_click=_load_draft).props("outline")
            ui.button("Share", on_click=_create_submit)
            ui.button("Cancel", on_click=create_dialog.close).props("outline")

    def _open_create_dialog() -> None:
        _apply_path_draft(app.storage.user.get(path_draft_key))
        create_dialog.open()

    return create_dialog, create_course_ids, _open_create_dialog


async def open_edit_path_dialog(
    *,
    detail: dict[str, Any],
    course_by_id: dict[int, dict[str, Any]],
    detail_dialog: ui.dialog | None,
    on_save: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    """Open an edit-path dialog."""
    ordered_course_ids: list[int] = [
        int(c.get("id")) for c in (detail.get("courses") or []) if isinstance(c, dict) and c.get("id") is not None
    ]

    with ui.dialog() as edit_dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
        ui.label("Edit Path").classes("text-xl font-semibold")

        name = ui.input("Name", value=str(detail.get("name") or "")).props("clearable").classes("w-full")
        description = ui.textarea("Description", value=str(detail.get("description") or "")).props("autogrow").classes("w-full")

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
                await on_save(payload)
                ui.notify("Path updated", type="positive")
                edit_dialog.close()
                if detail_dialog is not None:
                    detail_dialog.close()

            ui.button("Save", on_click=_save)
            ui.button("Cancel", on_click=edit_dialog.close).props("outline")

    edit_dialog.open()
