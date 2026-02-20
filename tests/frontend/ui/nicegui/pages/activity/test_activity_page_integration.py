from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.activity import page as activity_page


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self._handlers: dict[str, Any] = {}

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
        self.last_radio: _FakeElement | None = None
        self.navigate = SimpleNamespace(to=lambda _path: None)
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={"tab": "inbox"})))

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, _text: str = "") -> _FakeElement:
        return _FakeElement()

    def radio(self, _options: dict[str, str], value: str) -> _FakeElement:
        el = _FakeElement(value=value)
        self.last_radio = el
        return el

    def button(self, _label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement()
        if on_click is not None:
            el.on("click", on_click)
        return el

    def refreshable(self, fn):  # noqa: ANN001
        return _FakeRefreshable(fn)

    def row(self):
        return _FakeContainer()

    def notify(self, _message: str, *, type: str = "info") -> None:  # noqa: A002
        return None


@pytest.mark.anyio
async def test_activity_tab_change_during_load_queues_followup_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(activity_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(activity_page, "render_container", _container)
    monkeypatch.setattr(activity_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "require_user", _require_user)
    monkeypatch.setattr(activity_page, "render_empty_activity", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "render_activity_items", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "render_activity_error", lambda **_kwargs: None)

    calls: list[str] = []
    switched = False

    class _Api:
        async def get(self, path: str, params: dict[str, Any] | None = None):  # noqa: ANN001
            nonlocal switched
            if path == "/notifications/activity":
                calls.append(str((params or {}).get("scope") or ""))
                if not switched and (params or {}).get("scope") == "inbox" and fake_ui.last_radio is not None:
                    switched = True
                    fake_ui.last_radio.value = "team"
                    await fake_ui.last_radio.emit("update:model-value")
            return [{"message": "ok", "target_id": 1}]

    activity_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/activity"]
    await handler()

    assert calls == ["inbox", "team"]


@pytest.mark.anyio
async def test_activity_queue_runs_followup_even_if_first_load_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(activity_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(activity_page, "render_container", _container)
    monkeypatch.setattr(activity_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "require_user", _require_user)
    monkeypatch.setattr(activity_page, "render_empty_activity", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "render_activity_items", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "render_activity_error", lambda **_kwargs: None)

    calls: list[str] = []
    failed_once = False
    switched = False

    class _Api:
        async def get(self, path: str, params: dict[str, Any] | None = None):  # noqa: ANN001
            nonlocal failed_once, switched
            if path == "/notifications/activity":
                scope = str((params or {}).get("scope") or "")
                calls.append(scope)
                if not switched and scope == "inbox" and fake_ui.last_radio is not None:
                    switched = True
                    fake_ui.last_radio.value = "team"
                    await fake_ui.last_radio.emit("update:model-value")
                if not failed_once and scope == "inbox":
                    failed_once = True
                    raise RuntimeError("inbox failed")
            return [{"message": "ok", "target_id": 1}]

    activity_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/activity"]
    await handler()

    assert calls == ["inbox", "team"]


@pytest.mark.anyio
async def test_activity_failed_tab_load_clears_events_and_renders_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(activity_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(activity_page, "render_container", _container)
    monkeypatch.setattr(activity_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(activity_page, "require_user", _require_user)
    monkeypatch.setattr(activity_page, "render_empty_activity", lambda **_kwargs: None)

    item_renders: list[int] = []
    error_renders: list[str] = []
    monkeypatch.setattr(activity_page, "render_activity_items", lambda **kwargs: item_renders.append(len(kwargs["events"])))
    monkeypatch.setattr(activity_page, "render_activity_error", lambda **kwargs: error_renders.append(str(kwargs["message"])))

    class _Api:
        async def get(self, path: str, params: dict[str, Any] | None = None):  # noqa: ANN001
            if path == "/notifications/activity" and (params or {}).get("scope") == "team":
                raise RuntimeError("team failed")
            return [{"message": "ok", "target_id": 1}]

    activity_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    handler = fake_ui.routes["/activity"]
    await handler()

    assert item_renders
    fake_ui.last_radio.value = "team"  # type: ignore[union-attr]
    await fake_ui.last_radio.emit("update:model-value")  # type: ignore[union-attr]
    assert error_renders
    assert any("team failed" in msg for msg in error_renders)
