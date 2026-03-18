"""UI orchestration for learning-item share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.helpers import normalize_requested_share_type, share_subtitle_for_type
from frontend.ui.nicegui.pages.share.page_item_article_actions import wire_article_actions
from frontend.ui.nicegui.pages.share.page_item_course_actions import wire_course_actions
from frontend.ui.nicegui.pages.share.page_item_drafts import (
    refresh_title_suggestion,
    wire_article_draft,
    wire_course_draft,
)
from frontend.ui.nicegui.pages.share.page_item_form import (
    build_article_controls,
    build_course_controls,
    render_share_scaffold,
    render_share_type_picker,
)
from frontend.ui.nicegui.pages.share.state import ShareArticleUiState, ShareCourseUiState


async def render_share_item_page(
    *,
    user: dict[str, Any],
    store: Any,
    api: Any,
    controller: SharePageController,
    item_type: str,
    ui_module: Any,
    app_module: Any,
    render_shell_fn: Any,
    render_catalog_scope_fn: Any,
    notify: Any,
) -> None:
    """Render the dedicated learning-item share route."""
    username = str(user.get("username") or "")
    normalized_type = normalize_requested_share_type(item_type)
    render_shell_fn(title="Share Learning Item", store=store, api=api)
    with render_catalog_scope_fn(variant="explore").classes("lp-container lp-share-scope"):
        render_share_type_picker(ui_module=ui_module, current_type=normalized_type)
        render_share_scaffold(
            ui_module=ui_module,
            title="Share Learning Item",
            subtitle=share_subtitle_for_type(normalized_type),
        )
        if normalized_type == "article":
            draft_key = f"share_article_page_draft::{username}"
            state = ShareArticleUiState()
            controls = build_article_controls(ui_module=ui_module)
            wire_article_draft(controls=controls, draft_key=draft_key, app_module=app_module, notify=notify)
            wire_article_actions(
                controls=controls,
                state=state,
                controller=controller,
                draft_key=draft_key,
                app_module=app_module,
                ui_module=ui_module,
                notify=notify,
            )
            controls.preview.refresh()
            return

        draft_key = f"share_{normalized_type}_page_draft::{username}"
        state = ShareCourseUiState()
        controls = build_course_controls(ui_module=ui_module, item_type=normalized_type)
        wire_course_draft(
            controls=controls,
            draft_key=draft_key,
            item_type=normalized_type,
            app_module=app_module,
            notify=notify,
        )
        wire_course_actions(
            controls=controls,
            state=state,
            controller=controller,
            draft_key=draft_key,
            item_type=normalized_type,
            app_module=app_module,
            ui_module=ui_module,
            notify=notify,
        )
        refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()
