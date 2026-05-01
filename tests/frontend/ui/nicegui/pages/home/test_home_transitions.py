from __future__ import annotations

from frontend.ui.nicegui.pages.shared_stats.transitions import (
    begin_shared_stats_load,
    finalize_shared_stats_load,
    should_render_team_stats,
)


def test_begin_shared_stats_load_defaults() -> None:
    out = begin_shared_stats_load()
    assert out.loading is True
    assert out.meta_text == "Loading..."


def test_finalize_shared_stats_load_success() -> None:
    out = finalize_shared_stats_load(ok=True)
    assert out.loading is False
    assert out.meta_text == "Updated"


def test_finalize_shared_stats_load_failure() -> None:
    out = finalize_shared_stats_load(ok=False)
    assert out.loading is False
    assert out.meta_text == "Failed to load"


def test_should_render_team_stats_rules() -> None:
    assert should_render_team_stats(is_admin=True, mode_value="team") is True
    assert should_render_team_stats(is_admin=True, mode_value="mine") is False
    assert should_render_team_stats(is_admin=False, mode_value="team") is False
