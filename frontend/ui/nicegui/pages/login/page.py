"""Login page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.login.controller import LoginPageController
from frontend.ui.nicegui.pages.login.state import LoginPageState
from frontend.ui.nicegui.pages.login.transitions import begin_login_submit, finalize_login_submit
from frontend.ui.nicegui.pages.login.ui_glue import credentials_valid, normalize_credentials


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/login` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/login")
    async def login_page() -> None:
        controller = LoginPageController(store=store, api=api)
        if controller.is_authenticated():
            ui.navigate.to("/home")
            return

        state = LoginPageState()
        with render_container():
            ui.element("div").classes("lp-login-bg")
            with ui.card().classes("lp-card w-[min(460px,95vw)] mx-auto"):
                ui.label("Learning Hub").classes("lp-brand text-2xl font-semibold")
                ui.label("Sign in to continue.").classes("text-sm text-gray-600")

                username = ui.input("Username").props("autofocus clearable").classes("w-full")
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
                login_btn = ui.button("Login")

                with ui.row().classes("justify-end w-full mt-2"):

                    @guard_ui_action(title="Login failed")
                    async def _submit() -> None:
                        if state.loading:
                            return
                        u, p = normalize_credentials(username=str(username.value or ""), password=str(password.value or ""))
                        if not credentials_valid(username=u, password=p):
                            safe_notify("Username and password are required.", type="warning")
                            return
                        start = begin_login_submit()
                        state.loading = start.loading
                        login_btn.disable()
                        try:
                            await controller.submit_login(username=u, password=p)
                            track_ui_event_nowait(
                                api=api,
                                event_name="login_success",
                                context={"username": str(u)},
                            )
                            ui.navigate.to("/home")
                        finally:
                            done = finalize_login_submit()
                            state.loading = done.loading
                            login_btn.enable()

                    login_btn.on_click(_submit)

                async def _submit_from_enter(*_args: Any) -> None:
                    await _submit()

                username.on("keydown.enter", _submit_from_enter)
                password.on("keydown.enter", _submit_from_enter)
