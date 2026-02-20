"""UI sections for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_actions import render_view_review_actions
from frontend.ui.nicegui.pages.articles.ui_glue import ActiveFilterChip


@dataclass
class ArticlesFilterControls:
    """Filter controls rendered in the articles rail."""

    tag_filter: Any
    author_filter: Any
    refresh_btn: Any


def render_filters_rail(
    *,
    on_refresh: Any,
    on_reset: Any,
) -> ArticlesFilterControls:
    """Render articles filter rail and return control handles."""
    with ui.row().classes("items-center justify-between w-full"):
        ui.label("Filters").classes("text-md font-semibold")
        refresh_btn = ui.button("Refresh", on_click=on_refresh).props("outline dense")

    ui.label("Tip: share useful resources with colleagues.").classes("text-xs").style("color: var(--lp-muted)")

    tag_filter = ui.select({"": "Any tag"}, label="Tag", value="").props("dense").classes("w-full")
    author_filter = ui.select({"": "Anyone"}, label="Shared by", value="").props("dense").classes("w-full")
    ui.button("Reset all", on_click=on_reset).props("outline").classes("w-full mt-2")

    return ArticlesFilterControls(
        tag_filter=tag_filter,
        author_filter=author_filter,
        refresh_btn=refresh_btn,
    )


def render_active_filter_chips(
    *,
    chips: list[ActiveFilterChip],
    on_clear_key: Any,
) -> None:
    """Render removable active-filter chips."""
    if not chips:
        return

    def _chip(label: str, on_clear: Any) -> None:
        with ui.element("div").classes("lp-filter-chip"):
            ui.label(label)
            ui.button("×", on_click=on_clear).props("dense flat")

    with ui.row().classes("items-center gap-2 w-full flex-wrap"):
        for chip in chips:

            def _clear(_key: str = chip.key) -> None:
                on_clear_key(_key)

            _chip(chip.label, _clear)


def render_articles_empty_state(
    *,
    has_articles: bool,
    any_filters: bool,
    on_share: Any,
    on_reset: Any,
    on_refresh: Any,
) -> None:
    """Render empty states for the articles list."""
    if not has_articles and not any_filters:
        ui.label("No articles yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Share the first link to get started.").classes("text-sm").style("color: var(--lp-muted)")
        ui.button("Share an article", on_click=on_share).props("outline")
        return

    ui.label("No articles match your filters.").classes("text-sm").style("color: var(--lp-muted)")
    with ui.row().classes("items-center gap-2"):
        ui.button("Reset all", on_click=on_reset).props("outline")
        ui.button("Refresh", on_click=on_refresh).props("outline")


def render_article_card(
    *,
    article_row: dict[str, Any],
    is_new: bool,
    tags: list[str],
    summary_text: str,
    subtitle_text: str,
    view_action: Any,
    review_action: Any,
) -> None:
    """Render one article card with actions."""
    title = str(article_row.get("title") or "").strip()
    url = str(article_row.get("url") or "").strip()

    with ui.card().classes("w-full lp-card lp-card--hover"):
        with ui.element("div").classes("lp-card-topright"):
            if is_new:
                ui.label("New").classes("lp-chip lp-chip--sky")

        ui.label(title).classes("text-lg font-semibold")
        if url:
            ui.link(url, url).props("target=_blank").classes("text-sm")

        ui.label(subtitle_text).classes("text-xs").style("color: var(--lp-muted)")

        if tags:
            with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                for t in tags[:10]:
                    ui.label(t).classes("lp-meta-chip")
                if len(tags) > 10:
                    ui.label(f"+{len(tags) - 10}").classes("lp-meta-chip")
        if summary_text:
            ui.label(summary_text).classes("lp-meta-chip")

        with ui.row().classes("items-center gap-2 mt-2"):
            render_view_review_actions(on_view=view_action, on_review=review_action, review_tooltip="Reviews")
