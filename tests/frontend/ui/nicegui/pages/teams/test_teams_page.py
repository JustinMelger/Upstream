from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from frontend.ui.nicegui.core.navigation import build_activity_target_link
from frontend.ui.nicegui.pages.teams.page_ui import _TeamsPageView
from frontend.ui.nicegui.pages.teams.state import TeamsPageState


def test_open_activity_target_navigates_to_typed_target_url(monkeypatch) -> None:  # noqa: ANN001
    navigated: list[str] = []
    fake_ui = SimpleNamespace(navigate=SimpleNamespace(to=lambda path: navigated.append(str(path))))
    monkeypatch.setattr("frontend.ui.nicegui.pages.teams.page_ui.ui", fake_ui)

    view = _TeamsPageView(
        controller=object(),  # type: ignore[arg-type]
        state=TeamsPageState(),
        username="alice",
        role="member",
        initial_tab="inbox",
    )

    target = SimpleNamespace(open_url="/explore/paths/9")
    view.open_activity_target(target)

    assert navigated == ["/explore/paths/9"]


def test_render_team_detail_view_renders_inbox_without_selected_team(monkeypatch) -> None:  # noqa: ANN001
    class _FakeContainer:
        def classes(self, _value: str):  # noqa: ANN001
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

    fake_ui = SimpleNamespace(
        column=lambda: _FakeContainer(),
        label=lambda _text="": _FakeContainer(),
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr("frontend.ui.nicegui.pages.teams.page_ui.ui", fake_ui)
    monkeypatch.setattr("frontend.ui.nicegui.pages.teams.page_ui.build_activity_event_views", lambda *, events: list(events))
    monkeypatch.setattr(
        "frontend.ui.nicegui.pages.teams.page_ui.render_activity_feed",
        lambda *, events, on_open, empty_title, empty_description, compact=True: captured.update(  # noqa: ARG005
            {
                "inbox_rows": events,
                "empty_title": empty_title,
                "empty_description": empty_description,
            }
        ),
    )
    monkeypatch.setattr(
        "frontend.ui.nicegui.pages.teams.page_ui.render_empty_block",
        lambda **kwargs: captured.update({"empty": kwargs}),
    )

    view = _TeamsPageView(
        controller=object(),  # type: ignore[arg-type]
        state=TeamsPageState(inbox_rows=[{"message": "Needs review", "target_type": "course", "target_id": 4}]),
        username="alice",
        role="member",
        initial_tab="inbox",
    )

    view._render_team_detail_view()

    assert captured["inbox_rows"] == [{"message": "Needs review", "target_type": "course", "target_id": 4}]
    assert captured["empty_title"] == "No conversations pending."
    assert "empty" not in captured


def test_bind_actions_tolerates_missing_view_tabs_for_empty_workspace() -> None:
    class _FakeButton:
        def __init__(self) -> None:
            self.clicked = None

        def on_click(self, handler):  # noqa: ANN001
            self.clicked = handler
            return self

    view = _TeamsPageView(
        controller=object(),  # type: ignore[arg-type]
        state=TeamsPageState(),
        username="alice",
        role="member",
        initial_tab="inbox",
    )
    view.create_team_btn = _FakeButton()
    view.refresh_btn = _FakeButton()
    view.view_tabs = None
    view.create_team_dialog = SimpleNamespace(open=lambda: None)

    view._bind_actions()

    assert view.create_team_btn.clicked is not None
    assert view.refresh_btn.clicked is not None


def test_member_mutations_refresh_full_teams_state() -> None:
    src = Path("frontend/ui/nicegui/pages/teams/page_ui.py").read_text(encoding="utf-8")
    assert 'safe_notify("Member updated.", type="positive")\n                await self.refresh_all()' in src
    assert 'safe_notify("Member removed.", type="positive")\n        await self.refresh_all()' in src


def test_activity_target_link_opens_article_detail() -> None:
    assert build_activity_target_link(target_type="article", target_id=7) == "/explore/articles/7"


def test_on_tab_change_does_not_navigate_for_current_route_tab(monkeypatch) -> None:  # noqa: ANN001
    navigated: list[str] = []
    fake_ui = SimpleNamespace(navigate=SimpleNamespace(to=lambda path: navigated.append(str(path))))
    monkeypatch.setattr("frontend.ui.nicegui.pages.teams.page_ui.ui", fake_ui)

    class _Refreshable:
        def refresh(self) -> None:
            return None

    class _Tabs:
        value = "inbox"

    class _Controller:
        async def list_inbox(self, *, limit: int) -> list[dict[str, object]]:  # noqa: ARG002
            return []

    view = _TeamsPageView(
        controller=_Controller(),  # type: ignore[arg-type]
        state=TeamsPageState(),
        username="alice",
        role="member",
        initial_tab="inbox",
    )
    view.current_route_tab = "inbox"
    view.view_tabs = _Tabs()
    view.team_detail_view = _Refreshable()

    import asyncio

    asyncio.run(view.on_tab_change())

    assert navigated == []
