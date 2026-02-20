from __future__ import annotations

from frontend.ui.nicegui.pages.home.transitions import begin_home_load, finalize_home_load, should_render_team_section


def test_begin_home_load_defaults() -> None:
    out = begin_home_load()
    assert out.loading is True
    assert out.meta_text == "Loading..."


def test_finalize_home_load_success() -> None:
    out = finalize_home_load(ok=True)
    assert out.loading is False
    assert out.meta_text == "Updated"


def test_finalize_home_load_failure() -> None:
    out = finalize_home_load(ok=False)
    assert out.loading is False
    assert out.meta_text == "Failed to load"


def test_should_render_team_section_rules() -> None:
    assert should_render_team_section(is_admin=True, mode_value="team") is True
    assert should_render_team_section(is_admin=True, mode_value="mine") is False
    assert should_render_team_section(is_admin=False, mode_value="team") is False
