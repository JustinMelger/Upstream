from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.login.controller import LoginPageController


@pytest.mark.unit
def test_login_controller_is_authenticated_reads_token() -> None:
    class _Store:
        def __init__(self, token: str | None):
            self._token = token

        def get_token(self) -> str | None:
            return self._token

    class _Api:
        pass

    assert LoginPageController(store=_Store("x"), api=_Api()).is_authenticated() is True  # type: ignore[arg-type]
    assert LoginPageController(store=_Store(None), api=_Api()).is_authenticated() is False  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.anyio
async def test_login_controller_submit_login_calls_store_login() -> None:
    calls: list[tuple[str, str]] = []

    class _Store:
        def get_token(self) -> str | None:
            return None

        async def login(self, _api, username: str, password: str):  # noqa: ANN001
            calls.append((username, password))

    class _Api:
        pass

    c = LoginPageController(store=_Store(), api=_Api())  # type: ignore[arg-type]
    await c.submit_login(username="alice", password="secret")
    assert calls == [("alice", "secret")]
