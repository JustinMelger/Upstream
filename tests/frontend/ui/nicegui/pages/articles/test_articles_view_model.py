from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from frontend.ui.nicegui.domains.articles.view_model import map_article_card_view


@pytest.mark.unit
def test_map_article_card_view_builds_tags_subtitle_and_summary() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "id": 7,
        "created_by": "alice",
        "created_at": (now - timedelta(days=1)).isoformat(),
        "tags": "fastapi, backend",
        "preview_image_url": "https://cdn.example.com/og.png",
    }
    summary = {"avg_rating": 4.5, "review_count": 2}

    vm = map_article_card_view(article_row=row, review_summary_row=summary)

    assert vm.is_new is True
    assert vm.tags == ["fastapi", "backend"]
    assert "Shared by alice" in vm.subtitle_text
    assert vm.summary_text.startswith("★ ")
    assert vm.thumbnail_url == "https://cdn.example.com/og.png"


@pytest.mark.unit
def test_map_article_card_view_handles_missing_values() -> None:
    vm = map_article_card_view(article_row={"id": 9}, review_summary_row=None)
    assert vm.tags == []
    assert vm.summary_text == ""
    assert vm.thumbnail_url == ""
