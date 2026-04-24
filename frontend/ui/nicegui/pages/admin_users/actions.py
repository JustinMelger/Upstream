"""Action and load helpers for the Admin Users page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController
from frontend.ui.nicegui.pages.admin_users.state import AdminUsersPageState
from frontend.ui.nicegui.pages.admin_users.transitions import begin_admin_users_load, finalize_admin_users_load
from frontend.ui.nicegui.pages.admin_users.ui_glue import filter_users, user_row


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
    refresh_btn: Any
    create_btn: Any
    reset_btn: Any
    delete_btn: Any
    status_btn: Any


@dataclass(slots=True)
class AdminUsersPageContext:
    """Mutable page context shared across admin-user helpers."""

    controller: AdminUsersPageController
    state: AdminUsersPageState
    controls: AdminUsersControls


def apply_filter(ctx: AdminUsersPageContext) -> None:
    """Apply current search filter to the user table."""
    filtered = filter_users(ctx.state.users, str(ctx.controls.search.value or ""))
    ctx.controls.table.rows = [user_row(user) for user in filtered]
    ctx.controls.table.update()


async def load_users(ctx: AdminUsersPageContext) -> None:
    """Load users from backend and refresh the rendered table."""
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
        apply_filter(ctx)


async def create_user_action(ctx: AdminUsersPageContext, *, notify: Any) -> None:
    """Create a user from the current form fields."""
    username = str(ctx.controls.new_username.value or "").strip()
    password = str(ctx.controls.new_password.value or "").strip()
    role = str(ctx.controls.new_role.value or "user").strip()
    if not username or not password:
        notify("Username and password are required.", type="negative")
        return
    try:
        await ctx.controller.create_user(username=username, password=password, role=role)
        notify("User created.", type="positive")
        ctx.controls.new_username.value = ""
        ctx.controls.new_password.value = ""
        ctx.controls.new_role.value = "user"
        await load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 409:
            notify("User already exists.", type="negative")
            return
        raise


async def reset_password_action(ctx: AdminUsersPageContext, *, notify: Any) -> None:
    """Reset a user password from the current form fields."""
    username = str(ctx.controls.reset_username.value or "").strip()
    password = str(ctx.controls.reset_password.value or "").strip()
    if not username or not password:
        notify("Username and new password are required.", type="negative")
        return
    try:
        await ctx.controller.reset_password(username=username, password=password)
        notify("Password updated.", type="positive")
        ctx.controls.reset_username.value = ""
        ctx.controls.reset_password.value = ""
        await load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            notify("User not found.", type="negative")
            return
        raise


async def delete_user_action(ctx: AdminUsersPageContext, *, notify: Any) -> None:
    """Delete a user from the current form fields."""
    username = str(ctx.controls.delete_username.value or "").strip()
    if not username:
        notify("Username is required.", type="negative")
        return
    if not bool(ctx.controls.confirm_delete.value):
        notify("Confirm delete to continue.", type="negative")
        return
    try:
        await ctx.controller.delete_user(username=username)
        notify("User deleted.", type="positive")
        ctx.controls.delete_username.value = ""
        ctx.controls.confirm_delete.value = False
        await load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            notify("User not found.", type="negative")
            return
        raise


async def set_disabled_action(ctx: AdminUsersPageContext, *, notify: Any) -> None:
    """Disable or enable a user from the current form fields."""
    username = str(ctx.controls.disable_username.value or "").strip()
    if not username:
        notify("Username is required.", type="negative")
        return
    disabled = str(ctx.controls.disable_action.value or "disable") == "disable"
    try:
        await ctx.controller.set_disabled(username=username, disabled=disabled)
        notify("User updated.", type="positive")
        ctx.controls.disable_username.value = ""
        ctx.controls.disable_action.value = "disable"
        await load_users(ctx)
    except ApiError as exc:
        if exc.status_code == 404:
            notify("User not found.", type="negative")
            return
        raise
