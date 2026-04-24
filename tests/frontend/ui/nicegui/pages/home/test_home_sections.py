from __future__ import annotations

from frontend.ui.nicegui.pages.home import sections as home_sections


class _FakeElement:
    def classes(self, _value: str) -> "_FakeElement":
        return self


class _FakeContainer(_FakeElement):
    def __enter__(self) -> "_FakeContainer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeUi:
    def __init__(self) -> None:
        self.labels: list[str] = []

    def separator(self) -> _FakeElement:
        return _FakeElement()

    def label(self, text: str = "") -> _FakeElement:
        self.labels.append(str(text))
        return _FakeElement()

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def table(self, **_kwargs) -> _FakeElement:  # noqa: ANN003
        return _FakeElement()

    def echart(self, *_args, **_kwargs) -> _FakeElement:  # noqa: ANN002, ANN003
        return _FakeElement()


def test_render_admin_team_section_empty_state_explains_how_data_will_appear(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(home_sections, "ui", fake_ui)

    home_sections.render_admin_team_section(team_stats_by_user=[], contributors=[])

    assert "No team stats yet. Invite teammates and start sharing learning items to see progress here." in fake_ui.labels
    assert (
        "No contributor activity yet. Shares and reviews will appear here once your team is active."
        in fake_ui.labels
    )
