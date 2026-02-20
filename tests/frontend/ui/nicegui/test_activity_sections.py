from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.activity import sections as activity_sections


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

    def column(self) -> _FakeContainer:
        return _FakeContainer()

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def label(self, _text: str = "") -> _FakeElement:
        return _FakeElement()

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        self.buttons.append((label, on_click))
        return _FakeElement()


def test_render_activity_items_skips_invalid_target_id_and_logs_warning(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(activity_sections, "ui", fake_ui)

    warnings: list[dict[str, Any] | None] = []

    class _Logger:
        def warning(self, _message: str, *, extra: dict[str, Any] | None = None) -> None:
            warnings.append(extra)

    monkeypatch.setattr(activity_sections, "logger", _Logger())

    opened: list[tuple[str, int]] = []
    activity_sections.render_activity_items(
        events=[
            {"message": "bad", "target_type": "course", "target_id": "bad"},
            {"message": "ok", "target_type": "course", "target_id": 4},
        ],
        on_open=lambda t, tid: opened.append((t, tid)),
    )

    assert len(warnings) == 1
    assert isinstance(warnings[0], dict)
    assert len(fake_ui.buttons) == 1
