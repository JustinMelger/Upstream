"""Login page for the NiceGUI frontend."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/login` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/login")
    async def login_page() -> None:
        store.clear()
        with render_container():
            with ui.card().classes("lp-card w-[min(460px,95vw)] mx-auto"):
                ui.label("Login").classes("text-2xl font-semibold")
                ui.label("Sign in to continue.").classes("text-sm text-gray-600")

                username = ui.input("Username").props("autofocus clearable").classes("w-full")
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

                with ui.row().classes("justify-end w-full mt-2"):

                    @guard_ui_action(title="Login failed")
                    async def _submit() -> None:
                        await store.login(api, username=str(username.value or ""), password=str(password.value or ""))
                        ui.navigate.to("/")

                    ui.button("Login", on_click=_submit)
