"""Admin users page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController
from frontend.ui.nicegui.pages.admin_users.sections import USERS_TABLE_COLUMNS
from frontend.ui.nicegui.pages.admin_users.state import AdminUsersPageState
from frontend.ui.nicegui.pages.admin_users.transitions import begin_admin_users_load, finalize_admin_users_load
from frontend.ui.nicegui.pages.admin_users.ui_glue import _filter_users, _user_row


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

        controller = AdminUsersPageController(api=api)
        state = AdminUsersPageState()

        render_shell(title="Admin", store=store, api=api)
        with render_container():
            ui.label("Manage users and admin settings.").classes("text-sm text-gray-600")

            search = ui.input("Search users").props("clearable").classes("w-full")

            with ui.card().classes("lp-card w-full"):
                table = ui.table(columns=USERS_TABLE_COLUMNS, rows=[], row_key="username").classes("w-full")

            def _apply_filter() -> None:
                filtered = _filter_users(state.users, str(search.value or ""))
                table.rows = [_user_row(u) for u in filtered]
                table.update()

            @guard_ui_action(title="Load users failed")
            async def _load_users() -> None:
                if state.loading:
                    return
                load_start = begin_admin_users_load()
                state.loading = load_start.loading
                try:
                    rows = await controller.list_users()
                    load_done = finalize_admin_users_load(rows=rows)
                    state.users = list(load_done.users)
                except ApiError:
                    state.users = []
                    raise
                finally:
                    state.loading = False
                    _apply_filter()

            search.on("update:model-value", lambda *_: _apply_filter())

            with ui.row().classes("items-end w-full"):
                ui.button("Refresh", on_click=_load_users).props("outline")

            ui.separator()

            ui.label("Create user").classes("text-lg font-semibold")
            new_username = ui.input("Username").props("clearable").classes("w-full")
            new_password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
            new_role = ui.select({"user": "user", "admin": "admin"}, label="Role", value="user").classes("w-full")

            @guard_ui_action(title="Create user failed")
            async def _create_user() -> None:
                username = str(new_username.value or "").strip()
                password = str(new_password.value or "").strip()
                role = str(new_role.value or "user").strip()
                if not username or not password:
                    ui.notify("Username and password are required.", type="negative")
                    return
                try:
                    await controller.create_user(username=username, password=password, role=role)
                    ui.notify("User created.", type="positive")
                    new_username.value = ""
                    new_password.value = ""
                    new_role.value = "user"
                    await _load_users()
                except ApiError as exc:
                    if exc.status_code == 409:
                        ui.notify("User already exists.", type="negative")
                        return
                    raise

            ui.button("Create user", on_click=_create_user)

            ui.separator()

            ui.label("Reset password").classes("text-lg font-semibold")
            reset_username = ui.input("Username").props("clearable").classes("w-full")
            reset_password = ui.input("New password", password=True, password_toggle_button=True).classes("w-full")

            @guard_ui_action(title="Reset password failed")
            async def _reset_password() -> None:
                username = str(reset_username.value or "").strip()
                password = str(reset_password.value or "").strip()
                if not username or not password:
                    ui.notify("Username and new password are required.", type="negative")
                    return
                try:
                    await controller.reset_password(username=username, password=password)
                    ui.notify("Password updated.", type="positive")
                    reset_username.value = ""
                    reset_password.value = ""
                    await _load_users()
                except ApiError as exc:
                    if exc.status_code == 404:
                        ui.notify("User not found.", type="negative")
                        return
                    raise

            ui.button("Reset password", on_click=_reset_password).props("outline")

            ui.separator()

            ui.label("Delete user").classes("text-lg font-semibold")
            delete_username = ui.input("Username").props("clearable").classes("w-full")
            confirm_delete = ui.checkbox("Confirm delete")

            @guard_ui_action(title="Delete user failed")
            async def _delete_user() -> None:
                username = str(delete_username.value or "").strip()
                if not username:
                    ui.notify("Username is required.", type="negative")
                    return
                if not bool(confirm_delete.value):
                    ui.notify("Confirm delete to continue.", type="negative")
                    return
                try:
                    await controller.delete_user(username=username)
                    ui.notify("User deleted.", type="positive")
                    delete_username.value = ""
                    confirm_delete.value = False
                    await _load_users()
                except ApiError as exc:
                    if exc.status_code == 404:
                        ui.notify("User not found.", type="negative")
                        return
                    raise

            ui.button("Delete user", on_click=_delete_user).props("color=negative outline")

            ui.separator()

            ui.label("Disable user").classes("text-lg font-semibold")
            disable_username = ui.input("Username").props("clearable").classes("w-full")
            disable_action = ui.select({"disable": "Disable", "enable": "Enable"}, label="Action", value="disable")

            @guard_ui_action(title="Update user status failed")
            async def _set_disabled() -> None:
                username = str(disable_username.value or "").strip()
                if not username:
                    ui.notify("Username is required.", type="negative")
                    return
                disabled = str(disable_action.value or "disable") == "disable"
                try:
                    await controller.set_disabled(username=username, disabled=disabled)
                    ui.notify("User updated.", type="positive")
                    disable_username.value = ""
                    disable_action.value = "disable"
                    await _load_users()
                except ApiError as exc:
                    if exc.status_code == 404:
                        ui.notify("User not found.", type="negative")
                        return
                    raise

            ui.button("Update status", on_click=_set_disabled).props("outline")

            await _load_users()
