from __future__ import annotations

from frontend.ui.nicegui.core.navigation import (
    build_activity_tab_link,
    build_activity_target_link,
    build_courses_deep_link,
    build_learning_tab_link,
    build_paths_deep_link,
)
from frontend.ui.nicegui.core.navigation_intents import (
    get_catalog_share_storage_intent,
    pop_catalog_share_storage_intent,
    set_catalog_share_storage_intent,
)


def test_navigation_link_builders() -> None:
    assert build_courses_deep_link(course_id=12, view="reviews") == "/explore/courses/12?view=reviews"
    assert build_paths_deep_link(path_id=9, view="full") == "/explore/paths/9"
    assert build_learning_tab_link(tab="shared") == "/home?tab=shared"
    assert build_activity_tab_link(tab="team") == "/teams?tab=team"


def test_activity_target_link_builder() -> None:
    assert build_activity_target_link(target_type="course", target_id=7) == "/explore/courses/7"
    assert build_activity_target_link(target_type="video", target_id=5) == "/explore/videos/5"
    assert build_activity_target_link(target_type="path", target_id=2) == "/explore/paths/2"
    assert build_activity_target_link(target_type="article", target_id=1) == "/explore/articles/1"
    assert build_activity_target_link(target_type="unknown", target_id=1) == "/home"


def test_catalog_share_storage_intent_helpers_round_trip() -> None:
    storage: dict[str, object] = {}
    set_catalog_share_storage_intent(storage_user=storage, target="course")
    assert get_catalog_share_storage_intent(storage_user=storage) == "course"
    assert pop_catalog_share_storage_intent(storage_user=storage) == "course"
    assert get_catalog_share_storage_intent(storage_user=storage) is None

    set_catalog_share_storage_intent(storage_user=storage, target="invalid")
    assert get_catalog_share_storage_intent(storage_user=storage) is None
