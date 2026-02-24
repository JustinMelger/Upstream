from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.articles.detail_flow import open_article_details_flow
from frontend.ui.nicegui.pages.articles.state import ArticlesPageState


@pytest.mark.unit
@pytest.mark.anyio
async def test_open_article_details_flow_wires_controller_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    async def _open_article_details_dialog(**kwargs):  # noqa: ANN003
        captured.update(kwargs)

    from frontend.ui.nicegui.pages.articles import detail_flow as detail_flow_module

    monkeypatch.setattr(detail_flow_module, "open_article_details_dialog", _open_article_details_dialog)

    class _Controller:
        async def load_article_reviews(self, *, article_id: int):  # noqa: ANN001
            return [{"id": 1, "rating": 5}]

        async def save_article_review(self, *, article_id: int, rating: int, text: str):  # noqa: ANN001
            return {"id": 2, "rating": rating, "text": text}

        async def delete_article_review(self, *, article_id: int, review_id: int):  # noqa: ANN001
            return True

    state = ArticlesPageState(review_summary_by_article_id={7: {"article_id": 7, "review_count": 2}})

    await open_article_details_flow(
        article={"id": 7, "title": "Article"},
        focus_reviews=True,
        username="alice",
        is_admin=False,
        controller=_Controller(),
        state=state,
    )

    assert captured["article"]["id"] == 7
    assert captured["focus_reviews"] is True
    assert captured["review_summary_by_article_id"] is state.review_summary_by_article_id

    reviews = await captured["load_reviews"](7)
    saved = await captured["save_review"](7, 4, "nice")
    deleted = await captured["delete_review"](7, 3)
    assert reviews and int(reviews[0]["rating"]) == 5
    assert int(saved["rating"]) == 4
    assert deleted is True
