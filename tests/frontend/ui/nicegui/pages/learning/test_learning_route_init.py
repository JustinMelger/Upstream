from __future__ import annotations

from frontend.ui.nicegui.pages.learning.route_init import resolve_learning_initial_view


class _Req:
    def __init__(self, query_params: dict[str, str]):
        self.query_params = query_params


def test_resolve_learning_initial_view_defaults_learning() -> None:
    assert resolve_learning_initial_view(request=None) == "learning"


def test_resolve_learning_initial_view_accepts_shared_tab() -> None:
    req = _Req(query_params={"tab": "shared"})
    assert resolve_learning_initial_view(request=req) == "shared"


def test_resolve_learning_initial_view_normalizes_unknown_tab() -> None:
    req = _Req(query_params={"tab": "something_else"})
    assert resolve_learning_initial_view(request=req) == "learning"
