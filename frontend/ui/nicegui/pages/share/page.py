"""Dedicated share page routes."""

from __future__ import annotations

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.helpers import normalize_requested_share_type
from frontend.ui.nicegui.pages.share.page_item_ui import render_share_item_page
from frontend.ui.nicegui.pages.share.page_path_ui import render_share_path_page


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register dedicated learning-item share routes."""
    controller = SharePageController(api=api)

    @ui.page("/share/item")
    async def share_item_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        request = getattr(ui.context.client, "request", None)
        query_params = getattr(request, "query_params", None)
        item_type = normalize_requested_share_type(str((query_params or {}).get("type", "course")))
        await render_share_item_page(
            user=user,
            store=store,
            api=api,
            controller=controller,
            item_type=item_type,
            ui_module=ui,
            app_module=app,
            render_shell_fn=render_shell,
            render_catalog_scope_fn=render_catalog_scope,
            notify=safe_notify,
        )

    @ui.page("/share/path")
    async def share_path_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        await render_share_path_page(
            user=user,
            store=store,
            api=api,
            controller=controller,
            ui_module=ui,
            app_module=app,
            render_shell_fn=render_shell,
            render_catalog_scope_fn=render_catalog_scope,
            notify=safe_notify,
        )

    @ui.page("/share/course")
    async def share_course_compat_page() -> None:
        track_ui_event_nowait(
            api=api,
            event_name="share_compat_redirect_used",
            context={"from": "/share/course", "to": "/share/item", "item_type": "course"},
        )
        ui.navigate.to("/share/item?type=course")

    @ui.page("/share/article")
    async def share_article_compat_page() -> None:
        track_ui_event_nowait(
            api=api,
            event_name="share_compat_redirect_used",
            context={"from": "/share/article", "to": "/share/item", "item_type": "article"},
        )
        ui.navigate.to("/share/item?type=article")
