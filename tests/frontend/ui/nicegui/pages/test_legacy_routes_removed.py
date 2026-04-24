from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.explore import page as explore_page
from frontend.ui.nicegui.pages.home import page as home_page
from frontend.ui.nicegui.pages.learning import page as learning_page


class _FakeUi:
    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.navigate = SimpleNamespace(to=lambda _path, **_kwargs: None)
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))

    def page(self, path: str):  # noqa: ANN201
        def _decorator(fn):  # noqa: ANN001, ANN202
            self.routes[path] = fn
            return fn

        return _decorator


@pytest.mark.unit
def test_legacy_routes_are_not_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    for module in [home_page, learning_page, explore_page]:
        monkeypatch.setattr(module, "ui", fake_ui)

    async def _require_user(_store: object, _api: object) -> dict[str, str]:
        return {"username": "tester", "role": "admin"}

    for module in [home_page, learning_page, explore_page]:
        if hasattr(module, "require_user"):
            monkeypatch.setattr(module, "require_user", _require_user)
        module.register(store=object(), api=object())  # type: ignore[arg-type]

    for legacy_route in [
        "/learning",
        "/activity",
        "/insights",
        "/courses",
        "/paths",
        "/articles",
        "/manage/courses",
        "/manage/paths",
        "/manage/articles",
    ]:
        assert legacy_route not in fake_ui.routes
