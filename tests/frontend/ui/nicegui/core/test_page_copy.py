from __future__ import annotations

from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for


def test_primary_page_subtitles_are_defined() -> None:
    assert subtitle_for(PrimaryPage.HOME)
    assert subtitle_for(PrimaryPage.EXPLORE)
    assert subtitle_for(PrimaryPage.TEAMS)
    assert subtitle_for(PrimaryPage.PROFILE)


def test_home_subtitle_emphasizes_next_action() -> None:
    text = subtitle_for(PrimaryPage.HOME).lower()
    assert "what should i do next" in text
    assert "continue" in text
