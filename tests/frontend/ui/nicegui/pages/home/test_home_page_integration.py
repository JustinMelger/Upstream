from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.home import page as home_page


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self.text = ""
        self._handlers: dict[str, Any] = {}

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
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
        self.notifications: list[tuple[str, str]] = []
        self.navigate = SimpleNamespace(to=lambda _path: None)

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, text: str = "") -> _FakeElement:
        el = _FakeElement()
        el.text = text
        return el

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

    def card(self):
        return _FakeContainer()

    def separator(self) -> None:
        return None

    def notify(self, message: str, *, type: str = "info") -> None:
        self.notifications.append((message, type))


@pytest.mark.anyio
async def test_home_mode_change_during_load_queues_followup_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(home_page, "ui", fake_ui)

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(home_page, "render_container", _container)
    monkeypatch.setattr(home_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(home_page, "require_user", _require_user)
    monkeypatch.setattr(home_page, "render_inline_spinner", lambda **_kwargs: None)
    monkeypatch.setattr(home_page, "render_card_skeletons", lambda **_kwargs: None)
    monkeypatch.setattr(home_page, "_render_snapshot_metrics", lambda **_kwargs: None)
    monkeypatch.setattr(home_page, "_top_contributors", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(home_page, "render_admin_team_section", lambda **_kwargs: None)

    calls: list[tuple[str, dict[str, str] | None]] = []
    switched = False

    class _Api:
        async def get(self, path: str, params: dict[str, str] | None = None):  # noqa: ANN001
            nonlocal switched
            calls.append((path, params))
            if (
                not switched
                and path == "/tracking/stats"
                and params == {"colleague_id": "admin"}
                and fake_ui.last_radio is not None
            ):
                switched = True
                fake_ui.last_radio.value = "team"
                await fake_ui.last_radio.emit("update:model-value")
            if path == "/tracking/stats/users":
                return [{"colleague_id": "u1", "interested": 1, "in_progress": 0, "completed": 0}]
            return {"interested": 1, "in_progress": 2, "completed": 3}

    home_page.register(store=object(), api=_Api())  # type: ignore[arg-type]
    insights = fake_ui.routes["/insights"]
    await insights()

    assert calls[0] == ("/tracking/stats", {"colleague_id": "admin"})
    assert ("/tracking/stats", None) in calls
    assert ("/tracking/stats/users", None) in calls
    assert len(calls) == 3
