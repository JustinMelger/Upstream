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
        with ui.row().classes("items-center justify-between w-full gap-3 flex-wrap"):
            with ui.column().classes("gap-1"):
                ui.label("User directory").classes("text-lg font-semibold")
                ui.label("Search, inspect, and refresh current user access.").classes("text-xs text-gray-600")
            refresh_btn = ui.button("Refresh").props("outline")
        search = ui.input("Search users").props("clearable").classes("w-full")
        table = ui.table(columns=USERS_TABLE_COLUMNS, rows=[], row_key="username").classes("w-full")

    with ui.card().classes("lp-card w-full"):
        with ui.column().classes("gap-1"):
            ui.label("User actions").classes("text-lg font-semibold")
            ui.label("Create users, reset passwords, update access, or remove accounts.").classes("text-xs text-gray-600")

        tabs = ui.tabs().classes("w-full lp-admin-users-tabs")
        with tabs:
            ui.tab("Create")
            ui.tab("Reset password")
            ui.tab("Access")
            ui.tab("Delete")

        with ui.tab_panels(tabs, value="Create").classes("w-full lp-admin-users-panels"):
            with ui.tab_panel("Create").classes("gap-3 lp-admin-users-panel"):
                ui.label("Create user").classes("text-base font-semibold")
                ui.label("Add a new team member or administrator.").classes("text-xs text-gray-600")
                new_username = ui.input("Username").props("clearable").classes("w-full lp-admin-users-input")
                new_password = ui.input("Password", password=True, password_toggle_button=True).classes(
                    "w-full lp-admin-users-input"
                )
                new_role = ui.select({"user": "user", "admin": "admin"}, label="Role", value="user").classes(
                    "w-full lp-admin-users-input"
                )
                create_btn = ui.button("Create user")

            with ui.tab_panel("Reset password").classes("gap-3 lp-admin-users-panel"):
                ui.label("Reset password").classes("text-base font-semibold")
                ui.label("Set a new password for an existing account.").classes("text-xs text-gray-600")
                reset_username = ui.input("Username").props("clearable").classes("w-full lp-admin-users-input")
                reset_password = ui.input("New password", password=True, password_toggle_button=True).classes(
                    "w-full lp-admin-users-input"
                )
                reset_btn = ui.button("Reset password").props("outline")

            with ui.tab_panel("Access").classes("gap-3 lp-admin-users-panel"):
                ui.label("Access status").classes("text-base font-semibold")
                ui.label("Disable or re-enable an account without deleting it.").classes("text-xs text-gray-600")
                disable_username = ui.input("Username").props("clearable").classes("w-full lp-admin-users-input")
                disable_action = ui.select({"disable": "Disable", "enable": "Enable"}, label="Action", value="disable").classes(
                    "w-full lp-admin-users-input"
                )
                status_btn = ui.button("Update status").props("outline")

            with ui.tab_panel("Delete").classes("gap-3 lp-admin-users-panel"):
                ui.label("Delete user").classes("text-base font-semibold")
                ui.label("Permanent action. Use only when an account should be removed entirely.").classes(
                    "text-xs text-red-300"
                )
                delete_username = ui.input("Username").props("clearable").classes("w-full lp-admin-users-input")
                confirm_delete = ui.checkbox("Confirm delete")
                delete_btn = ui.button("Delete user").props("color=negative")

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
    ui.label("Manage access, passwords, and account status in one place.").classes("text-sm text-gray-600")
