"""Dialog builders for the Paths page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.path_items import build_path_item_payloads, decode_path_item_ref, encode_path_item_ref


def build_share_path_dialog(
    *,
    username: str,
    on_submit: Callable[[dict[str, Any]], Awaitable[None]],
) -> tuple[ui.dialog, Any, Callable[[], None]]:
    """Build the share-path dialog and return open helper + learning-item select handle."""
    path_draft_key = f"paths_share_draft::{username}"
    create_dialog = ui.dialog()
    with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label("Share Path").classes("text-xl font-semibold")
        ui.label("Save a draft if you want feedback before publishing.").classes("text-xs").style("color: var(--lp-muted)")
        create_name = ui.input("Name").props("clearable").classes("w-full")
        create_description = ui.textarea("Description").props("autogrow").classes("w-full")
        create_item_refs = ui.select({}, label="Learning items (ordered)", multiple=True).classes("w-full")

        def _path_draft_payload() -> dict[str, Any]:
            return {
                "name": str(create_name.value or ""),
                "description": str(create_description.value or ""),
                "item_refs": list(create_item_refs.value or []),
            }

        def _apply_path_draft(raw: Any) -> None:
            draft = raw if isinstance(raw, dict) else {}
            create_name.value = str(draft.get("name") or "")
            create_description.value = str(draft.get("description") or "")
            item_refs = list(draft.get("item_refs") or [])
            create_item_refs.value = item_refs
            create_item_refs.update()

        with ui.row().classes("justify-end mt-4"):

            def _save_draft() -> None:
                app.storage.user[path_draft_key] = _path_draft_payload()
                safe_notify("Draft saved", type="positive")

            def _load_draft() -> None:
                draft = app.storage.user.get(path_draft_key)
                if not isinstance(draft, dict):
                    safe_notify("No saved draft found", type="warning")
                    return
                _apply_path_draft(draft)
                safe_notify("Draft loaded", type="positive")

            @guard_ui_action(title="Share path failed")
            async def _create_submit() -> None:
                payload = {
                    "name": str(create_name.value or ""),
                    "description": str(create_description.value or ""),
                    "items": build_path_item_payloads(list(create_item_refs.value or [])),
                }
                await on_submit(payload)
                app.storage.user.pop(path_draft_key, None)
                safe_notify("Path shared", type="positive")
                create_dialog.close()

            ui.button("Save draft", on_click=_save_draft).props("outline")
            ui.button("Load draft", on_click=_load_draft).props("outline")
            ui.button("Share", on_click=_create_submit)
            ui.button("Cancel", on_click=create_dialog.close).props("outline")

    def _open_create_dialog() -> None:
        _apply_path_draft(app.storage.user.get(path_draft_key))
        create_dialog.open()

    return create_dialog, create_item_refs, _open_create_dialog


async def open_edit_path_dialog(
    *,
    detail: dict[str, Any],
    learning_item_options: dict[str, str],
    detail_dialog: ui.dialog | None,
    on_save: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    """Open an edit-path dialog."""
    ordered_item_refs = _ordered_item_refs_from_detail(detail)

    with ui.dialog() as edit_dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
        ui.label("Edit Path").classes("text-xl font-semibold")

        name = ui.input("Name", value=str(detail.get("name") or "")).props("clearable").classes("w-full")
        description = ui.textarea("Description", value=str(detail.get("description") or "")).props("autogrow").classes("w-full")

        ui.separator()
        ui.label("Learning Item Order").classes("text-lg font-semibold")

        add_course = ui.select(learning_item_options, label="Add learning item").classes("w-full")

        async def _add_course() -> None:
            _append_selected_item_ref(
                ordered_item_refs=ordered_item_refs,
                item_ref=str(add_course.value or "").strip(),
                refresh=courses_list.refresh,
            )

        ui.button("Add", on_click=_add_course).props("outline")

        @ui.refreshable
        def courses_list() -> None:
            _render_ordered_item_refs(
                ordered_item_refs=ordered_item_refs,
                learning_item_options=learning_item_options,
                refresh=courses_list.refresh,
            )

        courses_list()

        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Save changes failed")
            async def _save() -> None:
                payload = {
                    "name": str(name.value or ""),
                    "description": str(description.value or ""),
                    "items": build_path_item_payloads(ordered_item_refs),
                }
                await on_save(payload)
                safe_notify("Path updated", type="positive")
                edit_dialog.close()
                if detail_dialog is not None:
                    detail_dialog.close()

            ui.button("Save", on_click=_save)
            ui.button("Cancel", on_click=edit_dialog.close).props("outline")

    edit_dialog.open()


def _ordered_item_refs_from_detail(detail: dict[str, Any]) -> list[str]:
    """Extract ordered typed item refs from a path detail payload."""
    ordered_item_refs: list[str] = []
    for row in list(detail.get("items") or []):
        if not isinstance(row, dict):
            continue
        try:
            item_ref = encode_path_item_ref(item_type=str(row.get("type") or ""), item_id=int(row.get("id") or 0))
        except (TypeError, ValueError):
            continue
        ordered_item_refs.append(item_ref)
    return ordered_item_refs


def _append_selected_item_ref(*, ordered_item_refs: list[str], item_ref: str, refresh: Callable[..., Any]) -> None:
    """Append a selected learning-item ref when it is valid and not duplicated."""
    if not item_ref or item_ref in ordered_item_refs:
        return
    ordered_item_refs.append(item_ref)
    refresh()


def _display_title_for_item_ref(*, item_ref: str, learning_item_options: dict[str, str]) -> str:
    """Resolve a display title for one encoded item ref."""
    decoded = decode_path_item_ref(item_ref)
    if decoded is not None:
        item_type, item_id = decoded
        return learning_item_options.get(item_ref) or f"{item_type} #{item_id}"
    return learning_item_options.get(item_ref) or item_ref


def _render_ordered_item_ref_row(
    *,
    idx: int,
    item_ref: str,
    ordered_item_refs: list[str],
    learning_item_options: dict[str, str],
    refresh: Callable[..., Any],
) -> None:
    """Render one editable ordered learning-item row."""
    title = _display_title_for_item_ref(item_ref=item_ref, learning_item_options=learning_item_options)
    with ui.row().classes("items-center justify-between"):
        ui.label(f"{idx + 1}. {title}").classes("text-sm")
        with ui.row().classes("items-center"):

            def _move_up(_idx: int = idx) -> None:
                if _idx <= 0:
                    return
                ordered_item_refs[_idx - 1], ordered_item_refs[_idx] = ordered_item_refs[_idx], ordered_item_refs[_idx - 1]
                refresh()

            def _move_down(_idx: int = idx) -> None:
                if _idx >= len(ordered_item_refs) - 1:
                    return
                ordered_item_refs[_idx + 1], ordered_item_refs[_idx] = ordered_item_refs[_idx], ordered_item_refs[_idx + 1]
                refresh()

            def _remove(_item_ref: str = item_ref) -> None:
                if _item_ref in ordered_item_refs:
                    ordered_item_refs.remove(_item_ref)
                    refresh()

            ui.button("Up", on_click=_move_up).props("dense outline")
            ui.button("Down", on_click=_move_down).props("dense outline")
            ui.button("Remove", on_click=_remove).props("dense color=negative outline")


def _render_ordered_item_refs(
    *,
    ordered_item_refs: list[str],
    learning_item_options: dict[str, str],
    refresh: Callable[..., Any],
) -> None:
    """Render the ordered learning-item editor list."""
    with ui.column().classes("w-full gap-2"):
        if not ordered_item_refs:
            ui.label("No learning items selected.").classes("text-sm text-gray-600")
            return
        for idx, item_ref in enumerate(list(ordered_item_refs)):
            _render_ordered_item_ref_row(
                idx=idx,
                item_ref=item_ref,
                ordered_item_refs=ordered_item_refs,
                learning_item_options=learning_item_options,
                refresh=refresh,
            )
