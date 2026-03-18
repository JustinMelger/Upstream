from __future__ import annotations

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


def test_render_explore_empty_state_exposes_refresh_for_load_failure(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(list_sections, "ui", fake_ui)

    list_sections.render_explore_empty_state(
        loaded_once=False,
        on_refresh=lambda: None,
        on_reset_filters=lambda: None,
    )

    assert "Discovery feed unavailable" in fake_ui.labels
    assert "Explore could not load right now. Refresh to retry." in fake_ui.labels
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

    assert "No matches in Explore" in fake_ui.labels
    assert "Reset filters to widen your discovery results." in fake_ui.labels
    assert fake_ui.buttons[0][0] == "Reset filters"
    assert callable(fake_ui.buttons[0][1])
