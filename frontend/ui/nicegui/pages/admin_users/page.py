"""Admin users page for the NiceGUI frontend."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.admin_users.actions import (
    AdminUsersControls,
    AdminUsersPageContext,
    apply_filter,
    create_user_action,
    delete_user_action,
    load_users,
    reset_password_action,
    set_disabled_action,
)
from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController
from frontend.ui.nicegui.pages.admin_users.sections import build_admin_users_controls, render_admin_users_intro
from frontend.ui.nicegui.pages.admin_users.state import AdminUsersPageState


def _render_admin_users_actions(ctx: AdminUsersPageContext) -> None:
    search_handler = lambda *_: apply_filter(ctx)
    ctx.controls.search.on("update:model-value", search_handler)

    @guard_ui_action(title="Load users failed")
    async def _on_load_users() -> None:
        await load_users(ctx)

    @guard_ui_action(title="Create user failed")
    async def _on_create_user() -> None:
        await create_user_action(ctx, notify=safe_notify)

    @guard_ui_action(title="Reset password failed")
    async def _on_reset_password() -> None:
        await reset_password_action(ctx, notify=safe_notify)

    @guard_ui_action(title="Delete user failed")
    async def _on_delete_user() -> None:
        await delete_user_action(ctx, notify=safe_notify)

    @guard_ui_action(title="Update user status failed")
    async def _on_set_disabled() -> None:
        await set_disabled_action(ctx, notify=safe_notify)

    ctx.controls.refresh_btn.on_click(_on_load_users)
    ctx.controls.create_btn.on_click(_on_create_user)
    ctx.controls.reset_btn.on_click(_on_reset_password)
    ctx.controls.delete_btn.on_click(_on_delete_user)
    ctx.controls.status_btn.on_click(_on_set_disabled)


def _render_admin_users_body(ctx: AdminUsersPageContext) -> None:
    render_admin_users_intro()
    ctx.controls = build_admin_users_controls()
    _render_admin_users_actions(ctx)


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/admin/users` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/admin/users")
    async def admin_users_page() -> None:
        if await require_user(store, api, require_admin=True) is None:
            return

        ctx = AdminUsersPageContext(
            controller=AdminUsersPageController(api=api),
            state=AdminUsersPageState(),
            controls=AdminUsersControls(
                table=None,
                search=None,
                new_username=None,
                new_password=None,
                new_role=None,
                reset_username=None,
                reset_password=None,
                delete_username=None,
                confirm_delete=None,
                disable_username=None,
                disable_action=None,
                refresh_btn=None,
                create_btn=None,
                reset_btn=None,
                delete_btn=None,
                status_btn=None,
            ),
        )
        render_shell(title="Admin", store=store, api=api)
        with render_container():
            _render_admin_users_body(ctx)
            await load_users(ctx)
