from __future__ import annotations

from frontend.ui.nicegui.pages.articles.ui_glue import build_active_filter_chips, build_facet_select_options


def test_build_facet_select_options_sorts_and_formats_counts() -> None:
    tag_options, author_options = build_facet_select_options(
        tag_counts={"backend": 2, "api": 4},
        author_counts={"zoe": 1, "anna": 3},
    )
    assert tag_options[""] == "Any tag"
    assert list(tag_options.keys())[1:] == ["api", "backend"]
    assert author_options[""] == "Anyone"
    assert list(author_options.keys())[1:] == ["anna", "zoe"]


def test_build_active_filter_chips_includes_selected_filters() -> None:
    chips = build_active_filter_chips(
        search_value="fastapi",
        tag_value="backend",
        author_value="alice",
        sort_value="newest",
        sort_options={"newest": "Newest"},
    )
    assert [c.key for c in chips] == ["search", "tag", "author", "sort"]
    assert chips[-1].label == "Sort: Newest"
