from __future__ import annotations

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
