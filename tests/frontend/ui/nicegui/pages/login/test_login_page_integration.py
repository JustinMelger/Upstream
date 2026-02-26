from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.login import page as login_page


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self._handlers: dict[str, Any] = {}

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self

    def on_click(self, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers["click"] = handler
        return self

    def on(self, event: str, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers[event] = handler
        return self

    async def emit(self, event: str) -> None:
        handler = self._handlers.get(event)
        if handler is not None:
            await handler()

    def disable(self) -> None:
        return None

    def enable(self) -> None:
        return None


class _FakeContainer:
    def classes(self, _value: str) -> "_FakeContainer":
        return self

    def __enter__(self) -> "_FakeContainer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeUi:
    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.inputs: list[_FakeElement] = []
        self.buttons: dict[str, _FakeElement] = {}
        self.notifications: list[tuple[str, str]] = []
        self.navigations: list[str] = []
        self.navigate = SimpleNamespace(to=self.navigations.append)
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def element(self, _tag: str) -> _FakeElement:
        return _FakeElement()

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def label(self, _text: str = "") -> _FakeElement:
        return _FakeElement()

    def input(self, _label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="")
        self.inputs.append(el)
        return el

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement()
        if on_click is not None:
            el.on_click(on_click)
        self.buttons[label] = el
        return el

    def notify(self, message: str, *, type: str = "info") -> None:
        self.notifications.append((message, type))


@pytest.mark.anyio
async def test_login_page_redirects_when_token_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(login_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    monkeypatch.setattr(login_page, "render_container", _container)

    class _Store:
        def get_token(self) -> str | None:
            return "token"

        async def login(self, _api, username: str, password: str):  # noqa: ANN001
            return None

    class _Api:
        pass

    login_page.register(store=_Store(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/login"]
    await handler()

    assert fake_ui.navigations == ["/home"]


@pytest.mark.anyio
async def test_login_page_submit_calls_store_login_and_navigates(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(login_page, "ui", fake_ui)
    monkeypatch.setattr("frontend.ui.nicegui.core.errors.notify_error", lambda *_args, **_kwargs: None)

    @contextmanager
    def _container():
        yield

    monkeypatch.setattr(login_page, "render_container", _container)

    calls: list[tuple[str, str]] = []

    class _Store:
        def get_token(self) -> str | None:
            return None

        async def login(self, _api, username: str, password: str):  # noqa: ANN001
            calls.append((username, password))

    class _Api:
        pass

    login_page.register(store=_Store(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/login"]
    await handler()

    # Input creation order: username, password
    fake_ui.inputs[0].value = " alice "
    fake_ui.inputs[1].value = "secret"
    await fake_ui.buttons["Login"].emit("click")

    assert calls == [("alice", "secret")]
    assert "/home" in fake_ui.navigations
