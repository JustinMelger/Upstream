from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.components import catalog_hero as catalog_hero_components, layout as layout_components
from frontend.ui.nicegui.core import errors as core_errors
from frontend.ui.nicegui.pages.paths import page as paths_page, sections as paths_sections


class _FakeElement:
    def __init__(self, *, value: Any = None) -> None:
        self.value = value
        self.text = ""
        self.options: dict[Any, Any] = {}
        self._handlers: dict[str, Any] = {}

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self

    def style(self, _value: str) -> "_FakeElement":
        return self

    def tooltip(self, _value: str) -> "_FakeElement":
        return self

    def on(self, event: str, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers[event] = handler
        return self

    def update(self) -> None:
        return None

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
    def __init__(self, fn, ui_obj: "_FakeUi") -> None:  # noqa: ANN001
        self._fn = fn
        self._ui = ui_obj

    def refresh(self) -> None:
        self._ui.refresh_calls += 1
        self._fn()

    def __call__(self) -> None:
        self._fn()


@dataclass(slots=True)
class _RouteInit:
    initial_scope: str = "all"
    initial_path_id: int = 0
    initial_dialog_mode: str = "full"


class _FakeUi:
    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.refresh_calls = 0
        self.refresh_baseline = 0
        self.notifications: list[tuple[str, str]] = []
        self.navigate = SimpleNamespace(to=lambda _path, **_kwargs: None)
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, text: str = "") -> _FakeElement:
        el = _FakeElement()
        el.text = text
        return el

    def button(self, _label: str, on_click=None, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement()
        if on_click is not None:
            el.on("click", on_click)
        return el

    def row(self):
        return _FakeContainer()

    def column(self):
        return _FakeContainer()

    def card(self):
        return _FakeContainer()

    def element(self, _name: str):
        return _FakeContainer()

    def refreshable(self, fn):  # noqa: ANN001
        return _FakeRefreshable(fn, self)

    def notify(self, message: str, *, type: str = "info") -> None:  # noqa: A002
        self.notifications.append((message, type))


@pytest.mark.anyio
async def test_paths_track_does_not_refresh_list_before_select_post(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(paths_page, "ui", fake_ui)
    monkeypatch.setattr(layout_components, "ui", fake_ui)
    monkeypatch.setattr(catalog_hero_components, "ui", fake_ui)
    monkeypatch.setattr(paths_sections, "ui", fake_ui)
    monkeypatch.setattr(core_errors, "ui", fake_ui)
    monkeypatch.setattr(paths_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(paths_page, "render_container", _container)
    monkeypatch.setattr(paths_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "render_card_skeletons", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "require_user", _require_user)
    monkeypatch.setattr(paths_page, "collect_active_filter_chips", lambda **_kwargs: [])
    monkeypatch.setattr(paths_page, "resolve_paths_route_init", lambda **_kwargs: _RouteInit())
    monkeypatch.setattr(paths_page, "get_path_intent", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "intent_matches_path", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(paths_page, "pop_path_intent", lambda **_kwargs: None)

    async def _open_details_dialog(**_kwargs) -> None:  # noqa: ANN003
        return None

    monkeypatch.setattr(paths_page, "open_path_details_dialog", _open_details_dialog)

    captured_track_actions: list[Any] = []

    def _capture_path_card(**kwargs):  # noqa: ANN001
        captured_track_actions.append(kwargs["on_track_toggle"])

    monkeypatch.setattr(paths_page, "render_path_card", _capture_path_card)

    q = _FakeElement(value="")
    scope = _FakeElement(value="all")
    sort = _FakeElement(value="")
    sort.options = {}
    meta = _FakeElement()
    monkeypatch.setattr(paths_page, "render_paths_topbar", lambda **_kwargs: (q, scope, sort, meta))

    status_filter = _FakeElement(value="")
    status_filter.options = {}
    refresh_btn = _FakeElement()
    monkeypatch.setattr(paths_page, "render_paths_filter_rail", lambda **_kwargs: (status_filter, refresh_btn))

    create_course_ids = _FakeElement()
    create_course_ids.options = {}
    monkeypatch.setattr(
        paths_page,
        "build_share_path_dialog",
        lambda **_kwargs: (None, create_course_ids, (lambda: None)),
    )
    monkeypatch.setattr(paths_page, "render_split_layout", lambda **kwargs: (kwargs["rail"](), kwargs["main"]()))

    class _Api:
        def __init__(self) -> None:
            self.selected = False

        async def get(self, path: str, params: dict[str, Any] | None = None):  # noqa: ANN001
            if path == "/paths":
                return [{"id": 1, "name": "Path 1", "description": "", "created_by": "admin"}]
            if path == "/paths/selected/list":
                if self.selected:
                    return [{"id": 1, "name": "Path 1", "description": "", "status": "interested"}]
                return []
            if path == "/courses":
                return []
            if path == "/tracking":
                return []
            if path == "/paths/reviews/summary":
                return []
            if path == "/paths/recommendations/summary":
                return []
            if path == "/paths/1":
                return {"id": 1, "name": "Path 1", "description": "", "courses": []}
            return []

        async def post(self, path: str, payload: dict[str, Any] | None = None):  # noqa: ANN001
            if path == "/paths/1/select":
                # Regression guard: no eager refresh while this click handler is in-flight.
                assert fake_ui.refresh_calls == fake_ui.refresh_baseline
                self.selected = True
                return {"ok": True}
            return {"ok": True}

        async def put(self, path: str, payload: dict[str, Any] | None = None):  # noqa: ANN001
            return {"ok": True}

        async def delete(self, path: str):  # noqa: ANN001
            return {"ok": True}

    api = _Api()
    paths_page.register(store=object(), api=api)  # type: ignore[arg-type]
    handler = fake_ui.routes["/paths"]
    await handler()

    assert captured_track_actions, "Expected at least one rendered path card action"
    fake_ui.refresh_baseline = fake_ui.refresh_calls
    await captured_track_actions[0]()


@pytest.mark.anyio
async def test_paths_select_keeps_optimistic_state_when_selected_reload_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(paths_page, "ui", fake_ui)
    monkeypatch.setattr(layout_components, "ui", fake_ui)
    monkeypatch.setattr(catalog_hero_components, "ui", fake_ui)
    monkeypatch.setattr(paths_sections, "ui", fake_ui)
    monkeypatch.setattr(core_errors, "ui", fake_ui)
    monkeypatch.setattr(paths_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))

    @contextmanager
    def _container():
        yield

    async def _require_user(_store, _api):  # noqa: ANN001
        return {"username": "admin", "role": "admin"}

    monkeypatch.setattr(paths_page, "render_container", _container)
    monkeypatch.setattr(paths_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "render_card_skeletons", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "require_user", _require_user)
    monkeypatch.setattr(paths_page, "collect_active_filter_chips", lambda **_kwargs: [])
    monkeypatch.setattr(paths_page, "resolve_paths_route_init", lambda **_kwargs: _RouteInit())
    monkeypatch.setattr(paths_page, "get_path_intent", lambda **_kwargs: None)
    monkeypatch.setattr(paths_page, "intent_matches_path", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(paths_page, "pop_path_intent", lambda **_kwargs: None)

    async def _open_details_dialog(**_kwargs) -> None:  # noqa: ANN003
        return None

    monkeypatch.setattr(paths_page, "open_path_details_dialog", _open_details_dialog)

    captured_track_actions: list[Any] = []
    captured_labels: list[str] = []

    def _capture_path_card(**kwargs):  # noqa: ANN001
        captured_track_actions.append(kwargs["on_track_toggle"])
        captured_labels.append(str(kwargs["tracking_label_text"]))

    monkeypatch.setattr(paths_page, "render_path_card", _capture_path_card)

    q = _FakeElement(value="")
    scope = _FakeElement(value="all")
    sort = _FakeElement(value="")
    sort.options = {}
    meta = _FakeElement()
    monkeypatch.setattr(paths_page, "render_paths_topbar", lambda **_kwargs: (q, scope, sort, meta))

    status_filter = _FakeElement(value="")
    status_filter.options = {}
    refresh_btn = _FakeElement()
    monkeypatch.setattr(paths_page, "render_paths_filter_rail", lambda **_kwargs: (status_filter, refresh_btn))

    create_course_ids = _FakeElement()
    create_course_ids.options = {}
    monkeypatch.setattr(
        paths_page,
        "build_share_path_dialog",
        lambda **_kwargs: (None, create_course_ids, (lambda: None)),
    )
    monkeypatch.setattr(paths_page, "render_split_layout", lambda **kwargs: (kwargs["rail"](), kwargs["main"]()))

    class _Api:
        def __init__(self) -> None:
            self.selected = False
            self.fail_selected_list_once = False

        async def get(self, path: str, params: dict[str, Any] | None = None):  # noqa: ANN001
            if path == "/paths":
                return [{"id": 1, "name": "Path 1", "description": "", "created_by": "admin"}]
            if path == "/paths/selected/list":
                if self.fail_selected_list_once:
                    self.fail_selected_list_once = False
                    raise paths_page.ApiError(status_code=503, message="reload_failed")
                if self.selected:
                    return [{"id": 1, "name": "Path 1", "description": "", "status": "interested"}]
                return []
            if path == "/courses":
                return []
            if path == "/tracking":
                return []
            if path == "/paths/reviews/summary":
                return []
            if path == "/paths/recommendations/summary":
                return []
            if path == "/paths/1":
                return {"id": 1, "name": "Path 1", "description": "", "courses": []}
            return []

        async def post(self, path: str, payload: dict[str, Any] | None = None):  # noqa: ANN001
            if path == "/paths/1/select":
                self.selected = True
                self.fail_selected_list_once = True
                return {"ok": True}
            return {"ok": True}

        async def put(self, path: str, payload: dict[str, Any] | None = None):  # noqa: ANN001
            return {"ok": True}

        async def delete(self, path: str):  # noqa: ANN001
            return {"ok": True}

    api = _Api()
    paths_page.register(store=object(), api=api)  # type: ignore[arg-type]
    handler = fake_ui.routes["/paths"]
    await handler()

    assert captured_track_actions, "Expected at least one rendered path card action"
    await captured_track_actions[0]()

    assert "Tracked" in captured_labels
    assert any("selected list failed to refresh" in msg for msg, _kind in fake_ui.notifications)
