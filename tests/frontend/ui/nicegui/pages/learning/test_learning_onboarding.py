from __future__ import annotations

from frontend.ui.nicegui.pages.learning.onboarding import (
    dismiss_home_intro,
    HOME_INTRO_DISMISSED_KEY,
    INTRO_STEPS,
    should_show_home_intro,
)


def test_home_intro_has_three_steps() -> None:
    assert len(INTRO_STEPS) == 3
    assert all(str(step.title).strip() for step in INTRO_STEPS)
    assert all(str(step.body).strip() for step in INTRO_STEPS)
    assert "Explore" in INTRO_STEPS[0].body
    assert "Explore" in INTRO_STEPS[1].body
    assert "Teams" in INTRO_STEPS[2].body


def test_home_intro_visibility_and_dismiss_persistence() -> None:
    storage_user: dict[str, object] = {}
    assert should_show_home_intro(storage_user=storage_user) is True

    dismiss_home_intro(storage_user=storage_user)
    assert storage_user.get(HOME_INTRO_DISMISSED_KEY) is True
    assert should_show_home_intro(storage_user=storage_user) is False
