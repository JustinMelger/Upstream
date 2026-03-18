from __future__ import annotations

from frontend.ui.nicegui.pages.home.state import HomePageState
from frontend.ui.nicegui.pages.profile import page as profile_page


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

    def label(self, text: str = "") -> _FakeElement:
        self.labels.append(str(text))
        return _FakeElement()

    def element(self, _tag: str) -> _FakeContainer:
        return _FakeContainer()

    def card(self) -> _FakeContainer:
        return _FakeContainer()

    def row(self) -> _FakeContainer:
        return _FakeContainer()

    def echart(self, *_args, **_kwargs) -> _FakeElement:  # noqa: ANN002, ANN003
        return _FakeElement()

    def table(self, **_kwargs) -> _FakeElement:  # noqa: ANN003
        return _FakeElement()


class _DummyController:
    async def load_overview(self, **_kwargs):  # noqa: ANN003
        raise AssertionError("not used in this test")


def test_render_profile_team_sections_empty_state_points_to_next_steps(monkeypatch) -> None:  # noqa: ANN001
    fake_ui = _FakeUi()
    monkeypatch.setattr(profile_page, "ui", fake_ui)

    ctx = profile_page.ProfileStatsPageContext(
        username="alice",
        avatar_url="",
        avatar_initial="A",
        is_admin=True,
        controller=_DummyController(),  # type: ignore[arg-type]
        state=HomePageState(team_stats_by_user=[]),
        mode_value="team",
    )

    profile_page._render_profile_team_sections(ctx=ctx)

    assert (
        "No team contributor data yet. Open Teams to invite teammates or switch to My stats to review your own progress."
        in fake_ui.labels
    )
    assert (
        "No team stats available yet. Open Teams to build your workspace or switch to My stats to review your own activity."
        in fake_ui.labels
    )
