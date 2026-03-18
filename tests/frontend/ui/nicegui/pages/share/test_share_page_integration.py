from __future__ import annotations

from contextlib import contextmanager
import inspect
from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.pages.share import page as share_page


class _FakeElement:
    def __init__(self, *, value: Any = None, text: str = "", label: str = "") -> None:
        self.value = value
        self.text = text
        self.label = label
        self.visible = True
        self._handlers: dict[str, Any] = {}

    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self

    def style(self, _value: str) -> "_FakeElement":
        return self

    def on(self, event: str, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers[event] = handler
        return self

    def on_click(self, handler) -> "_FakeElement":  # noqa: ANN001
        self._handlers["click"] = handler
        return self

    async def emit(self, event: str) -> None:
        handler = self._handlers.get(event)
        if handler is None:
            return
        result = handler()
        if inspect.isawaitable(result):
            await result

    def update(self) -> None:
        return None


class _FakeContainer:
    def classes(self, _value: str) -> "_FakeContainer":
        return self

    def props(self, _value: str) -> "_FakeContainer":
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
        self.labels: list[_FakeElement] = []
        self.inputs: list[_FakeElement] = []
        self.buttons: list[str] = []
        self.button_map: dict[str, _FakeElement] = {}
        self.navigations: list[tuple[str, bool]] = []
        self.navigate = SimpleNamespace(to=lambda path, new_tab=False: self.navigations.append((path, bool(new_tab))))
        self.context = SimpleNamespace(client=SimpleNamespace(request=SimpleNamespace(query_params={})))

    def page(self, path: str):
        def _decorator(fn):
            self.routes[path] = fn
            return fn

        return _decorator

    def label(self, text: str = "") -> _FakeElement:
        el = _FakeElement(text=text)
        self.labels.append(el)
        return el

    def input(self, label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="", label=label)
        self.inputs.append(el)
        return el

    def textarea(self, label: str, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(value="", label=label)
        self.inputs.append(el)
        return el

    def button(self, label: str, on_click=None, **_kwargs) -> _FakeElement:  # noqa: ANN001
        el = _FakeElement(text=label)
        self.buttons.append(label)
        self.button_map[label] = el
        if on_click is not None:
            el.on_click(on_click)
        return el

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def column(self) -> _FakeContainer:
        return _FakeContainer()

    def separator(self) -> None:
        return None

    def refreshable(self, fn):  # noqa: ANN001
        return _FakeRefreshable(fn)


@contextmanager
def _fake_scope():
    yield _FakeContainer()


async def _fake_require_user(_store, _api):  # noqa: ANN001
    return {"username": "alice", "role": "admin"}


class _FakeController:
    def __init__(self) -> None:
        self.created_videos: list[dict[str, object]] = []
        self.created_courses: list[dict[str, object]] = []
        self.created_articles: list[dict[str, object]] = []

    async def suggest_course_from_url(self, *, url: str) -> dict[str, object]:
        return {
            "normalized_url": url,
            "suggested_learning_item_type": "video",
            "title": "Suggested video",
            "description": "Suggested description",
            "suggested_provider": "YouTube",
            "suggested_category": "Programming",
        }

    async def create_course(self, *, payload: dict[str, object]) -> dict[str, object]:
        self.created_courses.append(dict(payload))
        return dict(payload)

    async def suggest_video_from_url(self, *, url: str) -> dict[str, object]:
        return await self.suggest_course_from_url(url=url)

    async def create_video(self, *, payload: dict[str, object]) -> dict[str, object]:
        self.created_videos.append(dict(payload))
        return {"id": 12, **dict(payload)}

    async def suggest_article_from_url(self, *, url: str) -> dict[str, object]:
        return {"normalized_url": url, "title": "Suggested article", "suggested_tags": ["API", "Testing"]}

    async def create_article(self, *, payload: dict[str, object]) -> dict[str, object]:
        self.created_articles.append(dict(payload))
        return dict(payload)


@pytest.mark.anyio
async def test_share_item_video_route_renders_video_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    fake_ui.context.client.request.query_params = {"type": "video"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    assert "Video" in fake_ui.buttons
    assert "Course" in fake_ui.buttons
    assert "Article" in fake_ui.buttons
    assert any(label.text == "Share a video your team should learn from." for label in fake_ui.labels)
    assert any(inp.label == "Video title" for inp in fake_ui.inputs)


@pytest.mark.anyio
async def test_share_item_article_route_renders_article_specific_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    fake_ui.context.client.request.query_params = {"type": "article"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    assert any(label.text == "Share a useful article with your team." for label in fake_ui.labels)
    assert any(inp.label == "Article title" for inp in fake_ui.inputs)
    assert any(inp.label == "Tags (comma-separated)" for inp in fake_ui.inputs)


@pytest.mark.anyio
async def test_share_item_course_route_renders_course_specific_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    fake_ui.context.client.request.query_params = {"type": "course"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    assert any(label.text == "Share a course your team should learn from." for label in fake_ui.labels)
    assert any(inp.label == "Course title" for inp in fake_ui.inputs)
    assert any(inp.label == "Provider" for inp in fake_ui.inputs)
    assert any(inp.label == "Category" for inp in fake_ui.inputs)


@pytest.mark.anyio
async def test_share_item_video_import_populates_fields_and_detected_type(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    notifications: list[tuple[str, str]] = []
    fake_ui.context.client.request.query_params = {"type": "video"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user={})))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)
    monkeypatch.setattr(share_page, "safe_notify", lambda message, type="info": notifications.append((str(message), str(type))))

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    input_by_label = {element.label: element for element in fake_ui.inputs}
    input_by_label["https://..."].value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    await fake_ui.button_map["Import metadata"].emit("click")

    assert input_by_label["Video title"].value == "Suggested video"
    assert input_by_label["Description"].value == "Suggested description"
    assert input_by_label["Provider"].value == "YouTube"
    assert input_by_label["Category"].value == "Programming"
    assert any("Detected type: Video." == label.text for label in fake_ui.labels)
    assert notifications[-1] == ("Metadata imported", "positive")


@pytest.mark.anyio
async def test_share_item_course_publish_success_navigates_to_courses_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    notifications: list[tuple[str, str]] = []
    storage = {"share_course_page_draft::alice": {"title": "stale"}}
    fake_ui.context.client.request.query_params = {"type": "course"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user=storage)))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)
    monkeypatch.setattr(share_page, "safe_notify", lambda message, type="info": notifications.append((str(message), str(type))))

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    input_by_label = {element.label: element for element in fake_ui.inputs}
    input_by_label["https://..."].value = "https://www.udemy.com/course/fastapi-zero-to-prod/"
    input_by_label["Course title"].value = "Udemy FastAPI"
    input_by_label["Description"].value = "Strong structured course"
    input_by_label["Provider"].value = "Udemy"
    input_by_label["Category"].value = "Backend"
    await fake_ui.button_map["Publish Learning Item"].emit("click")

    assert controller.created_courses == [
        {
            "title": "Udemy FastAPI",
            "description": "Strong structured course",
            "provider": "Udemy",
            "category": "Backend",
            "url": "https://www.udemy.com/course/fastapi-zero-to-prod/",
        }
    ]
    assert "share_course_page_draft::alice" not in storage
    assert notifications[-1] == ("Learning item published", "positive")
    assert fake_ui.navigations[-1] == ("/explore?tab=courses", False)


@pytest.mark.anyio
async def test_share_item_video_publish_requires_description(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    notifications: list[tuple[str, str]] = []
    storage: dict[str, dict[str, str]] = {}
    fake_ui.context.client.request.query_params = {"type": "video"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user=storage)))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)
    monkeypatch.setattr(share_page, "safe_notify", lambda message, type="info": notifications.append((str(message), str(type))))

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    input_by_label = {element.label: element for element in fake_ui.inputs}
    input_by_label["https://..."].value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    input_by_label["Video title"].value = "Team video"
    await fake_ui.button_map["Publish Learning Item"].emit("click")

    assert controller.created_videos == []
    assert notifications[-1] == ("Description is required", "negative")
    assert fake_ui.navigations == []


@pytest.mark.anyio
async def test_share_item_article_publish_success_navigates_to_articles_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    notifications: list[tuple[str, str]] = []
    storage = {"share_article_page_draft::alice": {"title": "stale"}}
    fake_ui.context.client.request.query_params = {"type": "article"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user=storage)))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)
    monkeypatch.setattr(share_page, "safe_notify", lambda message, type="info": notifications.append((str(message), str(type))))

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    input_by_label = {element.label: element for element in fake_ui.inputs}
    input_by_label["https://..."].value = "https://fastapi.tiangolo.com/tutorial/testing/"
    input_by_label["Article title"].value = "FastAPI testing guide"
    input_by_label["Tags (comma-separated)"].value = "fastapi, testing"
    await fake_ui.button_map["Publish Learning Item"].emit("click")

    assert controller.created_articles == [
        {
            "title": "FastAPI testing guide",
            "url": "https://fastapi.tiangolo.com/tutorial/testing/",
            "tags": "fastapi, testing",
        }
    ]
    assert "share_article_page_draft::alice" not in storage
    assert notifications[-1] == ("Learning item published", "positive")
    assert fake_ui.navigations[-1] == ("/explore?tab=articles", False)


@pytest.mark.anyio
async def test_share_item_video_publish_success_navigates_and_persists_provider_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_ui = _FakeUi()
    controller = _FakeController()
    notifications: list[tuple[str, str]] = []
    storage = {"share_video_page_draft::alice": {"title": "stale"}}
    fake_ui.context.client.request.query_params = {"type": "video"}
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(share_page, "app", SimpleNamespace(storage=SimpleNamespace(user=storage)))
    monkeypatch.setattr(share_page, "render_shell", lambda **_kwargs: None)
    monkeypatch.setattr(share_page, "render_catalog_scope", lambda **_kwargs: _FakeContainer())
    monkeypatch.setattr(share_page, "require_user", _fake_require_user)
    monkeypatch.setattr(share_page, "SharePageController", lambda **_kwargs: controller)
    monkeypatch.setattr(share_page, "safe_notify", lambda message, type="info": notifications.append((str(message), str(type))))

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/item"]()

    input_by_label = {element.label: element for element in fake_ui.inputs}
    input_by_label["https://..."].value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    input_by_label["Video title"].value = "Team video"
    input_by_label["Description"].value = "Worth watching"
    await fake_ui.button_map["Publish Learning Item"].emit("click")

    assert controller.created_videos == [
        {
            "title": "Team video",
            "description": "Worth watching",
            "provider": "YouTube",
            "category": "",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
    ]
    assert "share_video_page_draft::alice" not in storage
    assert notifications[-1] == ("Learning item published", "positive")
    assert fake_ui.navigations[-1] == ("/explore/videos/12", False)


@pytest.mark.anyio
async def test_share_compat_routes_redirect_to_canonical_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ui = _FakeUi()
    tracked: list[tuple[str, dict[str, str]]] = []
    monkeypatch.setattr(share_page, "ui", fake_ui)
    monkeypatch.setattr(
        share_page,
        "track_ui_event_nowait",
        lambda *, api, event_name, context: tracked.append((str(event_name), dict(context))),  # noqa: ARG005
    )

    share_page.register(store=object(), api=object())  # type: ignore[arg-type]
    await fake_ui.routes["/share/course"]()
    await fake_ui.routes["/share/article"]()

    assert fake_ui.navigations == [
        ("/share/item?type=course", False),
        ("/share/item?type=article", False),
    ]
    assert tracked == [
        ("share_compat_redirect_used", {"from": "/share/course", "to": "/share/item", "item_type": "course"}),
        ("share_compat_redirect_used", {"from": "/share/article", "to": "/share/item", "item_type": "article"}),
    ]
