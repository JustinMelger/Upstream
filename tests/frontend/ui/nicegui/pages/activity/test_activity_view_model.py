from __future__ import annotations

from frontend.ui.nicegui.pages.shared_activity.view_model import build_activity_event_views, build_activity_target_view


def test_build_activity_target_view_maps_learning_items_and_paths() -> None:
    article_target = build_activity_target_view(target_type="article", target_id="7", target_label="Read this")
    video_target = build_activity_target_view(target_type="video", target_id="9", target_label="Watch this")
    path_target = build_activity_target_view(target_type="path", target_id=3, target_label="Backend path")

    assert article_target is not None
    assert article_target.target_family == "learning_item"
    assert article_target.target_type_label == "Article"
    assert article_target.interaction_label == "reviews"
    assert article_target.open_url == "/explore/articles/7"

    assert video_target is not None
    assert video_target.target_family == "learning_item"
    assert video_target.target_type_label == "Video"
    assert video_target.interaction_label == "reviews"
    assert video_target.open_url == "/explore/videos/9"

    assert path_target is not None
    assert path_target.target_family == "path"
    assert path_target.target_type_label == "Path"
    assert path_target.interaction_label == "path progress"
    assert path_target.open_url == "/explore/paths/3"


def test_build_activity_event_views_skips_invalid_targets() -> None:
    out = build_activity_event_views(
        events=[
            {"message": "bad", "target_type": "course", "target_id": "bad"},
            {"message": "ok", "actor": "alice", "target_type": "course", "target_id": 4, "target_label": "Course 1"},
        ]
    )

    assert len(out) == 1
    assert out[0].message == "ok"
    assert out[0].actor == "alice"
    assert out[0].target.target_type == "course"
    assert out[0].target.target_family == "learning_item"
