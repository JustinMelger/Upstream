from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.ai_curator import page as ai_curator_page


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self.text = ""
        self._handlers: dict[str, Any] = {}

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self

    def on_click(self, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers["click"] = handler
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


class _FakeRefreshable:
    def __init__(self, fn) -> None:  # noqa: ANN001
        self._fn = fn

    def refresh(self) -> None:
        self._fn()

    def __call__(self) -> None:
        self._fn()


class _FakeUi:
    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.inputs: list[_FakeElement] = []
        self.buttons: dict[str, _FakeElement] = {}
        self.labels: list[_FakeElement] = []
        self.notifications: list[tuple[str, str]] = []
        self.navigate = SimpleNamespace(to=lambda _path: None)
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, text: str = "") -> _FakeElement:
        el = _FakeElement()
        el.text = text
        self.labels.append(el)
        return el

    def input(self, _label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="")
        self.inputs.append(el)
        return el

    def textarea(self, _label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="")
        self.inputs.append(el)
        return el

    def checkbox(self, _label: str, value: bool = False) -> _FakeElement:
        return _FakeElement(value=value)

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement()
        if on_click is not None:
            el.on_click(on_click)
        self.buttons[label] = el
        return el

    def link(self, _label: str, _url: str) -> _FakeElement:
        return _FakeElement()

    def refreshable(self, fn):  # noqa: ANN001
        return _FakeRefreshable(fn)

    def row(self):
        return _FakeContainer()

    def column(self):
        return _FakeContainer()

    def card(self):
        return _FakeContainer()

    def separator(self) -> None:
        return None

    def notify(self, message: str, *, type: str = "info") -> None:
        self.notifications.append((message, type))

    def select(self, _options, **_kwargs) -> _FakeElement:  # noqa: ANN001
        return _FakeElement(value=None)


@pytest.mark.anyio
async def test_ai_curator_generate_error_updates_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(ai_curator_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "alice", "role": "admin"}

    monkeypatch.setattr(ai_curator_page, "render_container", _container)
    monkeypatch.setattr(ai_curator_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(ai_curator_page, "require_user", _require_user)
    monkeypatch.setattr("frontend.ui.nicegui.core.errors.notify_error", lambda *_args, **_kwargs: None)

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            if path == "/ai/plan":
                raise RuntimeError("plan failed")
            return {}

    ai_curator_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/ai"]
    await handler()

    # Input order: goal, path_name, path_description
    fake_ui.inputs[0].value = "Build APIs"
    await fake_ui.buttons["Generate"].emit("click")

    # The meta label is the second label in page setup.
    assert len(fake_ui.labels) >= 2
    assert fake_ui.labels[1].text == "Generation failed"
