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


def test_render_empty_activity_exposes_primary_explore_action(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_empty_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(activity_sections, "render_empty_block", _fake_render_empty_block)

    activity_sections.render_empty_activity(current_tab="team", on_primary=lambda: None)

    assert captured.get("primary_label") == "Explore"
    assert callable(captured.get("on_primary"))


def test_render_activity_error_exposes_retry_action(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_error_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(activity_sections, "render_error_block", _fake_render_error_block)

    activity_sections.render_activity_error(message="boom", on_retry=lambda: None)

    assert captured.get("retry_label") == "Retry"
    assert callable(captured.get("on_retry"))
