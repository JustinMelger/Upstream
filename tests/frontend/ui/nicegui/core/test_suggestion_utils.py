from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.suggestion_utils import suggestion_badge_text


@pytest.mark.unit
def test_suggestion_badge_text_empty_when_no_suggestion() -> None:
    assert suggestion_badge_text(current_value="any", suggested_value="") == ""


@pytest.mark.unit
def test_suggestion_badge_text_suggested_when_unchanged() -> None:
    assert suggestion_badge_text(current_value="FastAPI", suggested_value="FastAPI") == "Suggested"


@pytest.mark.unit
def test_suggestion_badge_text_edited_when_value_changed() -> None:
    assert suggestion_badge_text(current_value="FastAPI Advanced", suggested_value="FastAPI") == "Edited from suggestion"


@pytest.mark.unit
def test_suggestion_badge_text_edited_when_user_clears_suggested_value() -> None:
    assert suggestion_badge_text(current_value="", suggested_value="FastAPI") == "Edited from suggestion"
