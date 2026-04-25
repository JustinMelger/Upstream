"""UI sections/constants for Admin Users page."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.pages.admin_users.actions import AdminUsersControls


USERS_TABLE_COLUMNS: list[dict[str, str]] = [
    {"name": "username", "label": "Username", "field": "username"},
    {"name": "role", "label": "Role", "field": "role"},
    {"name": "created_at", "label": "Created at", "field": "created_at"},
    {"name": "updated_at", "label": "Updated at", "field": "updated_at"},
    {"name": "last_login_at", "label": "Last login", "field": "last_login_at"},
    {"name": "disabled", "label": "Disabled", "field": "disabled"},
]


def build_admin_users_controls() -> AdminUsersControls:
    """Build the full set of Admin Users form and table controls."""
    with ui.card().classes("lp-card w-full"):
        with ui.row().classes("items-end justify-between w-full gap-3 flex-wrap"):
            with ui.row().classes("items-center gap-2 grow min-w-[320px]"):
                ui.label("User directory").classes("text-lg font-semibold")
                search = ui.input("Search users").props("clearable").classes("w-full")
            refresh_btn = ui.button("Refresh").props("outline")

    with ui.card().classes("lp-card w-full"):
        ui.label("Current users").classes("text-lg font-semibold")
        ui.label("Search by username or role.").classes("text-xs text-gray-600")
        table = ui.table(columns=USERS_TABLE_COLUMNS, rows=[], row_key="username").classes("w-full")

    with ui.row().classes("w-full gap-4 items-start flex-wrap"):
        with ui.card().classes("lp-card grow min-w-[300px]"):
            ui.label("Create user").classes("text-lg font-semibold")
            ui.label("Add a new team member or administrator.").classes("text-xs text-gray-600")
            new_username = ui.input("Username").props("clearable").classes("w-full")
            new_password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
            new_role = ui.select({"user": "user", "admin": "admin"}, label="Role", value="user").classes("w-full")
            create_btn = ui.button("Create user")

        with ui.card().classes("lp-card grow min-w-[300px]"):
            ui.label("Reset password").classes("text-lg font-semibold")
            ui.label("Set a new password for an existing account.").classes("text-xs text-gray-600")
            reset_username = ui.input("Username").props("clearable").classes("w-full")
            reset_password = ui.input("New password", password=True, password_toggle_button=True).classes("w-full")
            reset_btn = ui.button("Reset password").props("outline")

    with ui.row().classes("w-full gap-4 items-start flex-wrap"):
        with ui.card().classes("lp-card grow min-w-[300px]"):
            ui.label("Access status").classes("text-lg font-semibold")
            ui.label("Disable or re-enable an account without deleting it.").classes("text-xs text-gray-600")
            disable_username = ui.input("Username").props("clearable").classes("w-full")
            disable_action = ui.select({"disable": "Disable", "enable": "Enable"}, label="Action", value="disable")
            status_btn = ui.button("Update status").props("outline")

        with ui.card().classes("lp-card grow min-w-[300px]"):
            ui.label("Delete user").classes("text-lg font-semibold")
            ui.label("Permanent action. Use only when an account should be removed entirely.").classes("text-xs text-gray-600")
            delete_username = ui.input("Username").props("clearable").classes("w-full")
            confirm_delete = ui.checkbox("Confirm delete")
            delete_btn = ui.button("Delete user").props("color=negative outline")

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
        refresh_btn=refresh_btn,
        create_btn=create_btn,
        reset_btn=reset_btn,
        delete_btn=delete_btn,
        status_btn=status_btn,
    )


def render_admin_users_intro() -> None:
    """Render the page intro copy."""
    ui.label("Admin users").classes("lp-home-title")
    ui.label("Manage access, passwords, and account status from one place.").classes("text-sm text-gray-600")
