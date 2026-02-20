from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.route_init import intent_matches_course, resolve_courses_route_init


class _Req:
    def __init__(self, query_params: dict[str, str]) -> None:
        self.query_params = query_params


@pytest.mark.unit
def test_resolve_courses_route_init_prefers_query_params() -> None:
    req = _Req({"tab": "tracked", "course_id": "42", "view": "reviews"})
    init = resolve_courses_route_init(
        request=req,
        storage_intent={"course_id": 7, "view": "full"},
        nav_intent={"course_id": 9, "view": "full"},
    )
    assert init.initial_scope == "tracked"
    assert init.initial_course_id == 42
    assert init.initial_focus_reviews is True


@pytest.mark.unit
def test_resolve_courses_route_init_falls_back_to_intents() -> None:
    req = _Req({})
    init = resolve_courses_route_init(
        request=req,
        storage_intent={"course_id": 11, "view": "reviews"},
        nav_intent={"course_id": 13, "view": "full"},
    )
    assert init.initial_scope == "all"
    assert init.initial_course_id == 11
    assert init.initial_focus_reviews is False


@pytest.mark.unit
def test_intent_matches_course_handles_invalid_and_valid_values() -> None:
    assert intent_matches_course({"course_id": "5"}, 5) is True
    assert intent_matches_course({"course_id": "bad"}, 5) is False
    assert intent_matches_course(None, 5) is False
