from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.core import errors as core_errors
from frontend.ui.nicegui.pages.admin_users import page as admin_users_page


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self._handlers: dict[str, Any] = {}
        self.rows: list[dict[str, Any]] = []

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self

    def on(self, event: str, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers[event] = handler
        return self

    def on_click(self, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers["click"] = handler
        return self

    async def emit(self, event: str) -> None:
        handler = self._handlers.get(event)
        if handler is not None:
            await handler()

    def update(self) -> None:
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
        self.selects: list[_FakeElement] = []
        self.buttons: dict[str, _FakeElement] = {}
        self.notifications: list[tuple[str, str]] = []
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))
        self.navigate = SimpleNamespace(to=lambda _path: None)

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, _text: str = "") -> _FakeElement:
        return _FakeElement()

    def input(self, _label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="")
        self.inputs.append(el)
        return el

    def select(self, _options, label: str | None = None, value: Any = None) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value=value)
        self.selects.append(el)
        return el

    def checkbox(self, _label: str) -> _FakeElement:
        return _FakeElement(value=False)

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement()
        if on_click is not None:
            el.on_click(on_click)
        self.buttons[label] = el
        return el

    def table(self, **_kwargs) -> _FakeElement:
        return _FakeElement()

    def row(self):
        return _FakeContainer()

    def card(self):
        return _FakeContainer()

    def separator(self) -> None:
        return None

    def notify(self, message: str, *, type: str = "info") -> None:
        self.notifications.append((message, type))


@pytest.mark.anyio
async def test_admin_users_create_user_flow_calls_create_and_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(admin_users_page, "ui", fake_ui)
    monkeypatch.setattr(core_errors, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api, require_admin: bool = False):  # noqa: ANN001
        assert require_admin is True
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(admin_users_page, "render_container", _container)
    monkeypatch.setattr(admin_users_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(admin_users_page, "require_user", _require_user)

    get_calls = 0
    post_calls: list[tuple[str, dict[str, Any]]] = []

    class _Api:
        async def get(self, path: str):  # noqa: ANN001
            nonlocal get_calls
            assert path == "/auth/users"
            get_calls += 1
            return [{"username": "seed", "role": "user"}]

        async def post(self, path: str, payload: dict[str, Any]):  # noqa: ANN001
            post_calls.append((path, payload))
            return {}

        async def delete(self, path: str):  # noqa: ANN001
            return {"removed": 1}

    admin_users_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/admin/users"]
    await handler()

    # Input creation order in page:
    # 0 search, 1 new_username, 2 new_password, 3 reset_username, 4 reset_password, 5 delete_username, 6 disable_username
    fake_ui.inputs[1].value = "alice"
    fake_ui.inputs[2].value = "secret"
    # Select creation order: 0 new_role, 1 disable_action
    fake_ui.selects[0].value = "admin"

    await fake_ui.buttons["Create user"].emit("click")

    assert ("/auth/users", {"username": "alice", "password": "secret", "role": "admin"}) in post_calls
    assert get_calls >= 2  # initial load + reload after create
    assert ("User created.", "positive") in fake_ui.notifications
