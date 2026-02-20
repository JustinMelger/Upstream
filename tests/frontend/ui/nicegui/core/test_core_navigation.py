from __future__ import annotations

from frontend.ui.nicegui.core.navigation import (
    build_activity_tab_link,
    build_activity_target_link,
    build_courses_deep_link,
    build_learning_tab_link,
    build_paths_deep_link,
)
from frontend.ui.nicegui.core.navigation_intents import (
    get_course_storage_intent,
    get_path_storage_intent,
    pop_course_storage_intent,
    pop_path_storage_intent,
    set_course_storage_intent,
    set_path_storage_intent,
)


def test_navigation_link_builders() -> None:
    assert build_courses_deep_link(course_id=12, view="reviews") == "/courses?tab=tracked&course_id=12&view=reviews"
    assert build_paths_deep_link(path_id=9, view="full") == "/paths?tab=selected&path_id=9&view=full"
    assert build_learning_tab_link(tab="shared") == "/learning?tab=shared"
    assert build_activity_tab_link(tab="team") == "/activity?tab=team"


def test_activity_target_link_builder() -> None:
    assert build_activity_target_link(target_type="course", target_id=7) == "/courses?course_id=7"
    assert build_activity_target_link(target_type="path", target_id=2) == "/paths?path_id=2"
    assert build_activity_target_link(target_type="article", target_id=1) == "/articles"
    assert build_activity_target_link(target_type="unknown", target_id=1) == "/learning"


def test_storage_intent_helpers_round_trip() -> None:
    storage: dict[str, object] = {}
    set_course_storage_intent(storage_user=storage, course_id=11, view="reviews")
    assert get_course_storage_intent(storage_user=storage) == {"course_id": 11, "view": "reviews"}
    assert pop_course_storage_intent(storage_user=storage) == {"course_id": 11, "view": "reviews"}
    assert get_course_storage_intent(storage_user=storage) is None

    set_path_storage_intent(storage_user=storage, path_id=5, view="full")
    assert get_path_storage_intent(storage_user=storage) == {"path_id": 5, "view": "full"}
    assert pop_path_storage_intent(storage_user=storage) == {"path_id": 5, "view": "full"}
    assert get_path_storage_intent(storage_user=storage) is None
