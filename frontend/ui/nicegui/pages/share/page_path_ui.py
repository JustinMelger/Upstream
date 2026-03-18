"""UI orchestration for path share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.page_path_actions import wire_path_actions, wire_path_draft
from frontend.ui.nicegui.pages.share.page_path_form import build_path_controls, render_share_scaffold


async def render_share_path_page(
    *,
    user: dict[str, Any],
    store: Any,
    api: Any,
    controller: SharePageController,
    ui_module: Any,
    app_module: Any,
    render_shell_fn: Any,
    render_catalog_scope_fn: Any,
    notify: Any,
) -> None:
    """Render the dedicated path share route."""
    username = str(user.get("username") or "")
    draft_key = f"share_path_page_draft::{username}"
    learning_item_options = await controller.load_path_learning_item_options()

    render_shell_fn(title="Share Path", store=store, api=api)
    with render_catalog_scope_fn(variant="explore").classes("lp-container lp-share-scope"):
        render_share_scaffold(
            ui_module=ui_module,
            title="Share Path",
            subtitle="Share a structured path your team can follow across courses, videos, and articles.",
        )
        controls = build_path_controls(ui_module=ui_module, learning_item_options=learning_item_options)
        wire_path_draft(controls=controls, draft_key=draft_key, app_module=app_module, notify=notify)
        wire_path_actions(
            controls=controls,
            controller=controller,
            draft_key=draft_key,
            app_module=app_module,
            ui_module=ui_module,
            notify=notify,
        )
        controls.preview.refresh()
