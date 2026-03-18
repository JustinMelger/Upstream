"""Admin users page for the NiceGUI frontend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController
from frontend.ui.nicegui.pages.admin_users.sections import USERS_TABLE_COLUMNS
from frontend.ui.nicegui.pages.admin_users.state import AdminUsersPageState
from frontend.ui.nicegui.pages.admin_users.transitions import begin_admin_users_load, finalize_admin_users_load
from frontend.ui.nicegui.pages.admin_users.ui_glue import _filter_users, _user_row


@dataclass(slots=True)
class AdminUsersControls:
    """UI handles used by `/admin/users` actions."""

    table: Any
    search: Any
    new_username: Any
    new_password: Any
    new_role: Any
    reset_username: Any
    reset_password: Any
    delete_username: Any
    confirm_delete: Any
    disable_username: Any
    disable_action: Any


@dataclass(slots=True)
class AdminUsersPageContext:
    """Mutable page context shared across admin-user helpers."""

    controller: AdminUsersPageController
    state: AdminUsersPageState
    controls: AdminUsersControls


def _apply_filter(ctx: AdminUsersPageContext) -> None:
    filtered = _filter_users(ctx.state.users, str(ctx.controls.search.value or ""))
    ctx.controls.table.rows = [_user_row(user) for user in filtered]
    ctx.controls.table.update()


async def _load_users(ctx: AdminUsersPageContext) -> None:
    if ctx.state.loading:
        return
    load_start = begin_admin_users_load()
    ctx.state.loading = load_start.loading
    try:
        rows = await ctx.controller.list_users()
        load_done = finalize_admin_users_load(rows=rows)
        ctx.state.users = list(load_done.users)
    except ApiError:
        ctx.state.users = []
        raise
    finally:
        ctx.state.loading = False
        _apply_filter(ctx)


async def _create_user(ctx: AdminUsersPageContext) -> None:
    username = str(ctx.controls.new_username.value or "").strip()
    password = str(ctx.controls.new_password.value or "").strip()
    role = str(ctx.controls.new_role.value or "user").strip()
    if not username or not password:
        safe_notify("Username and password are required.", type="negative")
        return
    try:
        await ctx.controller.create_user(username=username, password=password, role=role)
        safe_notify("User created.", type="positive")
        ctx.controls.new_username.value = ""
        ctx.controls.new_password.value = ""
        ctx.controls.new_role.value = "user"
        await _load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 409:
            safe_notify("User already exists.", type="negative")
            return
        raise


async def _reset_password(ctx: AdminUsersPageContext) -> None:
    username = str(ctx.controls.reset_username.value or "").strip()
    password = str(ctx.controls.reset_password.value or "").strip()
    if not username or not password:
        safe_notify("Username and new password are required.", type="negative")
        return
    try:
        await ctx.controller.reset_password(username=username, password=password)
        safe_notify("Password updated.", type="positive")
        ctx.controls.reset_username.value = ""
        ctx.controls.reset_password.value = ""
        await _load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            safe_notify("User not found.", type="negative")
            return
        raise


async def _delete_user(ctx: AdminUsersPageContext) -> None:
    username = str(ctx.controls.delete_username.value or "").strip()
    if not username:
        safe_notify("Username is required.", type="negative")
        return
    if not bool(ctx.controls.confirm_delete.value):
        safe_notify("Confirm delete to continue.", type="negative")
        return
    try:
        await ctx.controller.delete_user(username=username)
        safe_notify("User deleted.", type="positive")
        ctx.controls.delete_username.value = ""
        ctx.controls.confirm_delete.value = False
        await _load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            safe_notify("User not found.", type="negative")
            return
        raise


async def _set_disabled(ctx: AdminUsersPageContext) -> None:
    username = str(ctx.controls.disable_username.value or "").strip()
    if not username:
        safe_notify("Username is required.", type="negative")
        return
    disabled = str(ctx.controls.disable_action.value or "disable") == "disable"
    try:
        await ctx.controller.set_disabled(username=username, disabled=disabled)
        safe_notify("User updated.", type="positive")
        ctx.controls.disable_username.value = ""
        ctx.controls.disable_action.value = "disable"
        await _load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            safe_notify("User not found.", type="negative")
            return
        raise


def _build_admin_users_controls() -> AdminUsersControls:
    search = ui.input("Search users").props("clearable").classes("w-full")
    with ui.card().classes("lp-card w-full"):
        table = ui.table(columns=USERS_TABLE_COLUMNS, rows=[], row_key="username").classes("w-full")

    ui.separator()
    ui.label("Create user").classes("text-lg font-semibold")
    new_username = ui.input("Username").props("clearable").classes("w-full")
    new_password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
    new_role = ui.select({"user": "user", "admin": "admin"}, label="Role", value="user").classes("w-full")

    ui.separator()
    ui.label("Reset password").classes("text-lg font-semibold")
    reset_username = ui.input("Username").props("clearable").classes("w-full")
    reset_password = ui.input("New password", password=True, password_toggle_button=True).classes("w-full")

    ui.separator()
    ui.label("Delete user").classes("text-lg font-semibold")
    delete_username = ui.input("Username").props("clearable").classes("w-full")
    confirm_delete = ui.checkbox("Confirm delete")

    ui.separator()
    ui.label("Disable user").classes("text-lg font-semibold")
    disable_username = ui.input("Username").props("clearable").classes("w-full")
    disable_action = ui.select({"disable": "Disable", "enable": "Enable"}, label="Action", value="disable")

    return AdminUsersControls(
        table=table,
        search=search,
        new_username=new_username,
        new_password=new_password,
        new_role=new_role,
        reset_username=reset_username,
        reset_password=reset_password,
        delete_username=delete_username,
        confirm_delete=confirm_delete,
        disable_username=disable_username,
        disable_action=disable_action,
    )


def _render_admin_users_actions(ctx: AdminUsersPageContext) -> None:
    search_handler = lambda *_: _apply_filter(ctx)
    ctx.controls.search.on("update:model-value", search_handler)

    @guard_ui_action(title="Load users failed")
    async def _on_load_users() -> None:
        await _load_users(ctx)

    @guard_ui_action(title="Create user failed")
    async def _on_create_user() -> None:
        await _create_user(ctx)

    @guard_ui_action(title="Reset password failed")
    async def _on_reset_password() -> None:
        await _reset_password(ctx)

    @guard_ui_action(title="Delete user failed")
    async def _on_delete_user() -> None:
        await _delete_user(ctx)

    @guard_ui_action(title="Update user status failed")
    async def _on_set_disabled() -> None:
        await _set_disabled(ctx)

    with ui.row().classes("items-end w-full"):
        ui.button("Refresh", on_click=_on_load_users).props("outline")

    ui.button("Create user", on_click=_on_create_user)
    ui.button("Reset password", on_click=_on_reset_password).props("outline")
    ui.button("Delete user", on_click=_on_delete_user).props("color=negative outline")
    ui.button("Update status", on_click=_on_set_disabled).props("outline")


def _render_admin_users_body(ctx: AdminUsersPageContext) -> None:
    ui.label("Manage users and admin settings.").classes("text-sm text-gray-600")
    ctx.controls = _build_admin_users_controls()
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
            ),
        )
        render_shell(title="Admin", store=store, api=api)
        with render_container():
            _render_admin_users_body(ctx)
            await _load_users(ctx)
