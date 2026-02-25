from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.route_init import resolve_courses_route_init


class _Req:
    def __init__(self, query_params: dict[str, str]) -> None:
        self.query_params = query_params


@pytest.mark.unit
def test_resolve_courses_route_init_prefers_query_params() -> None:
    req = _Req({"tab": "tracked"})
    init = resolve_courses_route_init(request=req)
    assert init.initial_scope == "tracked"


@pytest.mark.unit
def test_resolve_courses_route_init_defaults_to_all_scope() -> None:
    req = _Req({})
    init = resolve_courses_route_init(request=req)
    assert init.initial_scope == "all"
