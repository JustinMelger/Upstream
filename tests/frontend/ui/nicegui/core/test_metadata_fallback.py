from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.metadata_fallback import build_article_metadata_fallback, build_course_metadata_fallback


@pytest.mark.unit
def test_build_course_metadata_fallback_uses_domain_label() -> None:
    out = build_course_metadata_fallback(url="https://www.realpython.com/some/path")
    assert out["provider"] == "Realpython"
    assert "Realpython" in out["title"]
    assert out["category"] == "Realpython"


@pytest.mark.unit
def test_build_article_metadata_fallback_uses_domain_label() -> None:
    out = build_article_metadata_fallback(url="https://docs.fastapi.tiangolo.com/tutorial/")
    assert "Docs" in out["title"]
    assert "docs" in out["tags"]
