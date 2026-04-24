"""Home page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.core.action_feedback import tracking_cleared_message, tracking_set_message
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.learning.controller import LearningPageController
from frontend.ui.nicegui.pages.learning.page_ui import (
    build_learning_page_context,
    render_learning_content,
    render_learning_intro_panel,
)
from frontend.ui.nicegui.pages.learning.route_init import resolve_learning_initial_view
from frontend.ui.nicegui.pages.learning.ui_glue import compute_next_visibility


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/home` route."""

    @ui.page("/home")
    async def learning_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Home", store=store, api=api)
        username = str(user.get("username") or "")
        page_ctx = build_learning_page_context(
            username=username,
            controller=LearningPageController(api=api),
        )
        request = getattr(ui.context.client, "request", None)
        initial_view = resolve_learning_initial_view(request=request)

        @guard_ui_action(title="Load failed")
        async def _load(*, reset_visibility: bool = True) -> None:
            if page_ctx.state.loading:
                return
            page_ctx.state.loading = True
            page_ctx.state.tracked_visible, page_ctx.state.selected_visible = compute_next_visibility(
                reset_visibility=bool(reset_visibility),
                page_size=int(page_ctx.state.page_size),
                tracked_visible=int(page_ctx.state.tracked_visible),
                selected_visible=int(page_ctx.state.selected_visible),
            )
            content.refresh()
            try:
                page_ctx.state.data = await page_ctx.controller.load_page_data(
                    username=username,
                    include_articles=bool(settings.feature_articles),
                )
            except ApiError as exc:
                safe_notify(str(exc), type="negative")
                page_ctx.state.data = {}
            finally:
                page_ctx.state.loading = False
                content.refresh()

        @guard_ui_action(title="Update tracking failed")
        async def _set_tracking_status(course_id: int, status: str) -> None:
            await page_ctx.controller.set_tracking_status(course_id=int(course_id), status=str(status))
            safe_notify(tracking_set_message(status=str(status)), type="positive")
            await _load(reset_visibility=False)

        @guard_ui_action(title="Update tracking failed")
        async def _clear_tracking_status(course_id: int) -> None:
            await page_ctx.controller.clear_tracking_status(course_id=int(course_id))
            safe_notify(tracking_cleared_message(), type="positive")
            await _load(reset_visibility=False)

        with render_catalog_scope(variant="explore").classes("lp-container lp-home-scope"):
            with ui.column().classes("w-full gap-1 lp-home-header"):
                ui.label(subtitle_for(PrimaryPage.HOME)).classes("text-sm text-gray-600 lp-home-header-kicker")
                ui.label("Learning dashboard").classes("lp-home-title")
                ui.label("Pick up the next useful learning action quickly.").classes("text-sm lp-home-header-subtitle").style(
                    "color: var(--lp-muted)"
                )

            render_learning_intro_panel()

            with ui.column().classes("lp-topbar lp-sticky-controls lp-home-topbar w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap lp-home-topbar-row"):
                    with ui.row().classes("items-center gap-3 w-full justify-end"):
                        view_filter = (
                            ui.radio({"learning": "Learning", "shared": "Shared"}, value=initial_view)
                            .props("inline dense")
                            .classes("text-sm")
                        )
                        ui.button("Refresh", on_click=_load).props("dense outline no-caps")

            def _navigate_tab() -> None:
                page_ctx.nav_actions.navigate_tab(str(view_filter.value or "learning"))

            def _on_view_tab_change(*_: Any) -> None:
                _navigate_tab()
                content.refresh()

            view_filter.on("update:model-value", _on_view_tab_change)

            @ui.refreshable
            def content() -> None:
                def _refresh_content() -> None:
                    content.refresh()

                render_learning_content(
                    page_ctx=page_ctx,
                    on_refresh=_refresh_content,
                    on_set_tracking_status=_set_tracking_status,
                    on_clear_tracking_status=_clear_tracking_status,
                    current_view=str(view_filter.value or "learning"),
                )

            await _load()
            content()
