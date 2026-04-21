from __future__ import annotations

from types import SimpleNamespace

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
        "frontend.ui.nicegui.pages.teams.page_ui.render_inbox_activity",
        lambda *, inbox_rows, on_open_target: captured.update(  # noqa: ARG005
            {"inbox_rows": inbox_rows}
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
    assert "empty" not in captured
