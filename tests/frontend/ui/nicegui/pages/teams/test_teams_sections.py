from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.shared_activity.view_model import build_activity_event_views
from frontend.ui.nicegui.pages.teams import sections as teams_sections


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

    def element(self, _tag: str) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def label(self, _text: str = "") -> _FakeElement:
        self.labels.append(str(_text))
        return _FakeElement()

    def icon(self, *_args: Any, **_kwargs: Any) -> _FakeElement:
        return _FakeElement()

    def button(self, label: str, on_click=None) -> _FakeElement:  # noqa: ANN001
        self.buttons.append((label, on_click))
        return _FakeElement()


def test_render_team_activity_uses_typed_target_open_action(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(teams_sections, "ui", fake_ui)

    opened: list[str] = []
    teams_sections.render_team_activity(
        activity_rows=build_activity_event_views(
            events=[{"message": "Shared", "actor": "alice", "target_type": "course", "target_id": 4}]
        ),
        on_open_target=lambda target: opened.append(str(target.open_url)),
    )

    assert len(fake_ui.buttons) == 1
    click = fake_ui.buttons[0][1]
    assert click is not None
    click()
    assert opened == ["/explore/courses/4"]
    assert "Course · tracking + reviews" in fake_ui.labels


def test_render_team_activity_empty_state_uses_learning_item_language(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_empty_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(teams_sections, "render_empty_block", _fake_render_empty_block)

    teams_sections.render_team_activity(activity_rows=[], on_open_target=lambda _target: None)

    assert captured.get("description") == "Share a learning item or path to start activity in this feed."


def test_render_teams_list_empty_state_has_one_clear_primary_action(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def _fake_render_empty_block(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(teams_sections, "render_empty_block", _fake_render_empty_block)

    teams_sections.render_teams_list(
        teams=[],
        selected_team_id=None,
        on_open=lambda _team_id: None,
        on_create_team=lambda: None,
    )

    assert captured.get("title") == "No teams yet."
    assert captured.get("primary_label") == "Create team"
    assert captured.get("on_primary") is not None
