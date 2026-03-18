from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.activity import sections as activity_sections
from frontend.ui.nicegui.pages.activity.view_model import build_activity_event_views


class _FakeElement:
    def classes(self, _value: str) -> "_FakeElement":
        return self

    def style(self, _value: str) -> "_FakeElement":
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
        self.buttons: list[tuple[str, Any]] = []
        self.labels: list[str] = []

    def column(self) -> _FakeContainer:
        return _FakeContainer()

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def label(self, _text: str = "") -> _FakeElement:
        self.labels.append(str(_text))
        return _FakeElement()

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        self.buttons.append((label, on_click))
        return _FakeElement()


def test_render_activity_items_renders_open_action_for_typed_events(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(activity_sections, "ui", fake_ui)

    opened: list[tuple[str, int]] = []
    activity_sections.render_activity_items(
        events=build_activity_event_views(
            events=[{"message": "ok", "target_type": "course", "target_id": 4, "target_label": "Course"}]
        ),
        on_open=lambda target: opened.append((str(target.target_type), int(target.target_id))),
    )

    assert len(fake_ui.buttons) == 1
    click = fake_ui.buttons[0][1]
    assert click is not None
    click()
    assert opened == [("course", 4)]
    assert "Course · tracking + reviews · Course" in fake_ui.labels


def test_render_empty_activity_exposes_primary_explore_action(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_empty_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(activity_sections, "render_empty_block", _fake_render_empty_block)

    activity_sections.render_empty_activity(current_tab="team", on_primary=lambda: None)

    assert captured.get("primary_label") == "Explore"
    assert callable(captured.get("on_primary"))
    assert captured.get("description") == "When teammates share, recommend, or rate learning items and paths, updates will appear here."


def test_render_activity_error_exposes_retry_action(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_error_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(activity_sections, "render_error_block", _fake_render_error_block)

    activity_sections.render_activity_error(message="boom", on_retry=lambda: None)

    assert captured.get("retry_label") == "Retry"
    assert callable(captured.get("on_retry"))
