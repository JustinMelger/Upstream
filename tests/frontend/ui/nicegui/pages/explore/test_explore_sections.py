from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.explore import list_sections


class _FakeElement:
    def classes(self, _value: str) -> "_FakeElement":
        return self

    def props(self, _value: str) -> "_FakeElement":
        return self


class _FakeContainer(_FakeElement):
    def __enter__(self) -> "_FakeContainer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeUi:
    def __init__(self) -> None:
        self.labels: list[str] = []
        self.buttons: list[tuple[str, Any]] = []

    def column(self) -> _FakeContainer:
        return _FakeContainer()

    def label(self, text: str = "") -> _FakeElement:
        self.labels.append(str(text))
        return _FakeElement()

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        self.buttons.append((label, on_click))
        return _FakeElement()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def element(self, _tag: str) -> _FakeContainer:
        return _FakeContainer()

    def link(self, _label: str, _target: str) -> _FakeElement:
        return _FakeElement()


@dataclass
class _FakeEntry:
    learning_item_type: str
    id: int
    row: dict[str, Any]


def test_render_explore_empty_state_exposes_refresh_for_load_failure(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(list_sections, "ui", fake_ui)

    list_sections.render_explore_empty_state(
        loaded_once=False,
        on_refresh=lambda: None,
        on_reset_filters=lambda: None,
    )

    assert "Explore is unavailable right now" in fake_ui.labels
    assert "Refresh to reload courses, paths, videos, and articles." in fake_ui.labels
    assert fake_ui.buttons[0][0] == "Refresh explore"
    assert callable(fake_ui.buttons[0][1])


def test_render_explore_empty_state_exposes_reset_for_filter_miss(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(list_sections, "ui", fake_ui)

    list_sections.render_explore_empty_state(
        loaded_once=True,
        on_refresh=lambda: None,
        on_reset_filters=lambda: None,
    )

    assert "No matching results" in fake_ui.labels
    assert "Reset filters to widen the current explore view." in fake_ui.labels
    assert fake_ui.buttons[0][0] == "Reset filters"
    assert callable(fake_ui.buttons[0][1])


def test_render_explore_sections_show_more_uses_full_learning_item_list(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    rendered_ids: list[int] = []
    monkeypatch.setattr(list_sections, "ui", fake_ui)
    monkeypatch.setattr(list_sections, "render_explore_course_spotlight", lambda **_: None)
    monkeypatch.setattr(
        list_sections, "render_article_item", lambda **kwargs: rendered_ids.append(int(kwargs["article"]["id"]))
    )
    monkeypatch.setattr(list_sections, "render_video_item", lambda **kwargs: rendered_ids.append(int(kwargs["video"]["id"])))
    monkeypatch.setattr(list_sections, "render_course_item", lambda **kwargs: rendered_ids.append(int(kwargs["course"]["id"])))
    monkeypatch.setattr(list_sections, "render_path_item", lambda **kwargs: None)

    entries = [
        _FakeEntry(
            learning_item_type="video" if index % 2 == 0 else "article",
            id=index,
            row={"id": index, "title": f"Item {index}"},
        )
        for index in range(1, 21)
    ]

    list_sections.render_explore_sections(
        shown_courses=[],
        shown_paths=[],
        shown_learning_items=entries,
        deps=list_sections.ExploreSectionsDeps(
            state=object(),
            username="alice",
            is_admin=False,
            show_all_categories=True,
            course_actions_builder=lambda *_: None,
            on_set_tracking=lambda *_: None,
            on_clear_tracking=lambda *_: None,
            on_toggle_path_selection=lambda *_: None,
            open_path=lambda *_: None,
            open_article_details=lambda *_: None,
            learning_items_visible_limit=8,
            on_show_more_learning_items=lambda: None,
        ),
    )

    assert rendered_ids == list(range(1, 9))
    assert any(label == "Show more learning items" for label, _ in fake_ui.buttons)
