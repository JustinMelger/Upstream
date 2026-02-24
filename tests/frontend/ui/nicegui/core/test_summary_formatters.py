from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.summary_formatters import format_recommendation_summary, format_review_summary


@pytest.mark.unit
def test_format_review_summary_fraction_and_star_styles() -> None:
    row = {"avg_rating": 4.25, "review_count": 3}
    assert format_review_summary(row, style="fraction") == "4.2/5 (3)"
    assert format_review_summary(row, style="star") == "★ 4.2 (3)"


@pytest.mark.unit
def test_format_review_summary_returns_empty_for_missing_or_zero() -> None:
    assert format_review_summary(None, style="fraction") == ""
    assert format_review_summary({"avg_rating": 4.0, "review_count": 0}, style="fraction") == ""


@pytest.mark.unit
def test_format_recommendation_summary_returns_badge_or_empty() -> None:
    assert format_recommendation_summary({"recommendation_count": 2}) == "↗ 2 rec"
    assert format_recommendation_summary({"recommendation_count": 0}) == ""
    assert format_recommendation_summary(None) == ""
