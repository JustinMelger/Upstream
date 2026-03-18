"""Draft and action wiring for path share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.pages.paths.item_helpers import build_path_item_payloads, encode_path_item_ref
from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.page_path_form import PathShareControls


def wire_path_draft(*, controls: PathShareControls, draft_key: str, app_module: Any, notify: Any) -> None:
    """Bind autosave/recovery behavior for path drafts."""

    def _save(*, show_notice: bool) -> None:
        app_module.storage.user[draft_key] = {
            "name": str(controls.name_input.value or ""),
            "description": str(controls.description_input.value or ""),
            "item_refs": list(controls.item_refs_input.value or []),
        }
        if show_notice:
            notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app_module.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.name_input.value = str(raw.get("name") or "")
        controls.description_input.value = str(raw.get("description") or "")
        item_refs = list(raw.get("item_refs") or [])
        if not item_refs:
            item_refs = [
                encode_path_item_ref(item_type="course", item_id=int(course_id))
                for course_id in list(raw.get("course_ids") or [])
            ]
        controls.item_refs_input.value = item_refs
        controls.item_refs_input.update()

    controls.save_btn.on("click", lambda *_: _save(show_notice=True))

    def _on_field_change(*_args: Any) -> None:
        _save(show_notice=False)
        controls.preview.refresh()

    for control in [controls.name_input, controls.description_input, controls.item_refs_input]:
        control.on("update:model-value", _on_field_change)

    _load()


def wire_path_actions(
    *,
    controls: PathShareControls,
    controller: SharePageController,
    draft_key: str,
    app_module: Any,
    ui_module: Any,
    notify: Any,
) -> None:
    """Bind publish behavior for path share routes."""

    @guard_ui_action(title="Publish failed")
    async def _publish() -> None:
        name = str(controls.name_input.value or "").strip()
        description = str(controls.description_input.value or "").strip()
        items = build_path_item_payloads(list(controls.item_refs_input.value or []))
        if not name:
            notify("Path name is required", type="negative")
            return
        if not items:
            notify("Select at least one learning item", type="negative")
            return
        created = await controller.create_path(
            payload={
                "name": name,
                "description": description,
                "items": items,
            }
        )
        app_module.storage.user.pop(draft_key, None)
        notify("Path published", type="positive")
        created_raw_id = created.get("id")
        created_id = created_raw_id if isinstance(created_raw_id, int) else 0
        ui_module.navigate.to(f"/explore/paths/{created_id}" if created_id > 0 else "/explore?tab=paths")

    controls.publish_btn.on("click", lambda *_: _publish())
