from __future__ import annotations

from frontend.ui.nicegui.pages.activity.route_init import resolve_activity_tab


class _Req:
    def __init__(self, query_params: dict[str, str]):
        self.query_params = query_params


def test_resolve_activity_tab_defaults_inbox() -> None:
    assert resolve_activity_tab(request=None) == "inbox"


def test_resolve_activity_tab_accepts_team() -> None:
    req = _Req(query_params={"tab": "team"})
    assert resolve_activity_tab(request=req) == "team"


def test_resolve_activity_tab_normalizes_unknown() -> None:
    req = _Req(query_params={"tab": "nope"})
    assert resolve_activity_tab(request=req) == "inbox"
