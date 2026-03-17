from __future__ import annotations

from types import SimpleNamespace

from frontend.ui.nicegui.pages.teams.page import _TeamsPageView
from frontend.ui.nicegui.pages.teams.state import TeamsPageState


def test_open_activity_target_navigates_to_typed_target_url(monkeypatch) -> None:  # noqa: ANN001
    navigated: list[str] = []
    fake_ui = SimpleNamespace(navigate=SimpleNamespace(to=lambda path: navigated.append(str(path))))
    monkeypatch.setattr("frontend.ui.nicegui.pages.teams.page.ui", fake_ui)

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
