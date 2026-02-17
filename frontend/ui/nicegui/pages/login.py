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
        # If the user is already authenticated, don't force a logout just by
        # visiting /login (e.g., via back button or a copied link).
        if store.get_token():
            ui.navigate.to("/learning")
            return

        with render_container():
            # Page-local background layer (see `.lp-login-bg` in `core/theme.py`).
            ui.element("div").classes("lp-login-bg")
            with ui.card().classes("lp-card w-[min(460px,95vw)] mx-auto"):
                ui.label("Learning Hub").classes("lp-brand text-2xl font-semibold")
                ui.label("Sign in to continue.").classes("text-sm text-gray-600")

                username = ui.input("Username").props("autofocus clearable").classes("w-full")
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
                loading = False
                login_btn = ui.button("Login")

                with ui.row().classes("justify-end w-full mt-2"):

                    @guard_ui_action(title="Login failed")
                    async def _submit() -> None:
                        nonlocal loading
                        if loading:
                            return
                        u = str(username.value or "").strip()
                        p = str(password.value or "")
                        if not u or not p:
                            ui.notify("Username and password are required.", type="warning")
                            return
                        loading = True
                        login_btn.disable()
                        try:
                            await store.login(api, username=u, password=p)
                            ui.navigate.to("/learning")
                        finally:
                            loading = False
                            login_btn.enable()

                    login_btn.on_click(_submit)

                # Support pressing Enter to submit from either field.
                username.on("keydown.enter", lambda *_: _submit())
                password.on("keydown.enter", lambda *_: _submit())
