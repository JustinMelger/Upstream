from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths.route_init import intent_matches_path, resolve_paths_route_init


class _Req:
    def __init__(self, query_params: dict[str, str]) -> None:
        self.query_params = query_params


@pytest.mark.unit
def test_resolve_paths_route_init_prefers_query_params() -> None:
    req = _Req({"tab": "selected", "path_id": "42", "view": "reviews"})
    init = resolve_paths_route_init(
        request=req,
        storage_intent={"path_id": 7, "view": "full"},
        nav_intent={"path_id": 9, "view": "full"},
        normalize_view_mode=lambda value: "reviews" if str(value) == "reviews" else "full",
    )
    assert init.initial_scope == "selected"
    assert init.initial_path_id == 42
    assert init.initial_dialog_mode == "reviews"


@pytest.mark.unit
def test_resolve_paths_route_init_falls_back_to_intents() -> None:
    req = _Req({})
    init = resolve_paths_route_init(
        request=req,
        storage_intent={"path_id": 11, "view": "reviews"},
        nav_intent={"path_id": 13, "view": "full"},
        normalize_view_mode=lambda value: "reviews" if str(value) == "reviews" else "full",
    )
    assert init.initial_scope == "all"
    assert init.initial_path_id == 11
    assert init.initial_dialog_mode == "full"


@pytest.mark.unit
def test_intent_matches_path_handles_invalid_and_valid_values() -> None:
    assert intent_matches_path({"path_id": "5"}, 5) is True
    assert intent_matches_path({"path_id": "bad"}, 5) is False
    assert intent_matches_path(None, 5) is False
