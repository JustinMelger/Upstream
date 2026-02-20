from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_articles_controller_load_list_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_load_articles(*, api):  # noqa: ANN001
        return [
            {"id": 1, "title": "A"},
            {"id": 2, "title": "B"},
        ]

    from frontend.ui.nicegui.pages.articles import controller as articles_controller

    monkeypatch.setattr(articles_controller, "load_articles", _fake_load_articles)

    class _Api:
        async def get(self, path: str, params: dict | None = None):  # noqa: ANN001
            assert path == "/articles/reviews/summary"
            assert params == {"article_ids": [1, 2]}
            return [
                {"article_id": 1, "avg_rating": 4.5, "review_count": 2},
                {"article_id": 2, "avg_rating": 5.0, "review_count": 1},
            ]

    c = ArticlesPageController(api=_Api())  # type: ignore[arg-type]
    bundle = await c.load_list_bundle()
    assert [int(a.get("id") or 0) for a in bundle.articles] == [1, 2]
    assert int((bundle.review_summary_by_article_id.get(1) or {}).get("review_count") or 0) == 2
    assert int((bundle.review_summary_by_article_id.get(2) or {}).get("review_count") or 0) == 1
