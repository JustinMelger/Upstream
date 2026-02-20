from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.articles.actions import build_article_card_actions


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_article_card_actions_wires_view_and_review_callbacks() -> None:
    calls: list[str] = []

    async def _open_details(article: dict, focus_reviews: bool) -> None:
        calls.append(f"{int(article.get('id') or 0)}:{focus_reviews}")

    actions = build_article_card_actions(
        article_row={"id": 5, "title": "X"},
        on_open_details=_open_details,
    )
    await actions.on_view()
    await actions.on_review()

    assert calls == ["5:False", "5:True"]
