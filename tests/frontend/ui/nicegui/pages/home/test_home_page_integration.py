from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.home import page as home_page


class _FakeUi:
    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.navigations: list[str] = []
        self.navigate = SimpleNamespace(to=self.navigations.append)

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator


@pytest.mark.anyio
async def test_root_redirects_to_login(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(home_page, "ui", fake_ui)

    home_page.register(store=object(), api=object())  # type: ignore[arg-type]
    handler = fake_ui.routes["/"]
    response = await handler()

    assert response.status_code == 307
    assert response.headers["location"] == "/login"


@pytest.mark.anyio
async def test_legacy_insights_route_is_not_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(home_page, "ui", fake_ui)

    home_page.register(store=object(), api=object())  # type: ignore[arg-type]
    assert "/insights" not in fake_ui.routes
