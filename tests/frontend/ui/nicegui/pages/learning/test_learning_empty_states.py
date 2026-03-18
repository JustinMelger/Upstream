from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.learning import sections as learning_sections


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
        self.labels: list[str] = []
        self.buttons: list[str] = []

    def column(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def element(self, _tag: str) -> _FakeContainer:
        return _FakeContainer()

    def icon(self, *_args: Any, **_kwargs: Any) -> _FakeElement:
        return _FakeElement()

    def separator(self) -> _FakeElement:
        return _FakeElement()

    def label(self, text: str = "") -> _FakeElement:
        self.labels.append(str(text))
        return _FakeElement()

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        self.buttons.append(str(label))
        return _FakeElement()


def test_render_conversations_section_empty_state_uses_learning_item_language(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(learning_sections, "ui", fake_ui)

    learning_sections.render_conversations_section(
        items=[],
        pending_course_review_ids=[],
        pending_path_review_ids=[],
        on_open_item=lambda _row: None,
        on_open_first_course_review=lambda: None,
        on_open_first_path_review=lambda: None,
    )

    assert "No conversations are waiting right now. Share a learning item or path to start team activity." in fake_ui.labels
