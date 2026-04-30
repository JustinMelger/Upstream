"""UI sections for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass
import html
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_frame import (
    render_card_actions_row,
    render_card_content_column,
    render_card_main_row,
    render_card_topright,
)
from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.pages.articles.ui_glue import ActiveFilterChip


@dataclass
class ArticlesFilterControls:
    """Filter controls rendered in the articles rail."""

    tag_filter: Any
    author_filter: Any
    refresh_btn: Any


@dataclass
class ArticlesTopbarControls:
    """Topbar controls rendered for articles page."""

    search_input: Any
    sort_filter: Any
    meta: Any


def render_articles_topbar(*, on_share: Any) -> ArticlesTopbarControls:
    """Render articles topbar and return controls."""
    with ui.column().classes("lp-topbar lp-sticky-controls lp-courses-toolbar w-full gap-2"):
        with ui.row().classes("w-full items-center gap-2"):
            search_input = (
                ui.input("Search articles")
                .props("clearable debounce=300 dense")
                .classes("lp-topbar-search lp-courses-search")
                .style("flex: 1")
            )
        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            meta = ui.label("").classes("lp-topbar-meta lp-topbar-count lp-topbar-meta--quiet")
            with ui.row().classes("items-center gap-2 justify-end flex-wrap"):
                with ui.row().classes(
                    "items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"
                ):
                    ui.label("Sort by").classes("lp-topbar-group-label")
                    sort_filter = (
                        ui.select(
                            {
                                "": "Best match",
                                "newest": "Newest",
                                "title_az": "Title A–Z",
                                "author_az": "Author A–Z",
                            },
                            value="",
                            label=None,
                        )
                        .props("dense")
                        .style("min-width: 180px")
                        .classes("lp-topbar-secondary-control")
                    )
                with ui.row().classes(
                    "items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"
                ):
                    topbar_menu = apply_icon_button_a11y(
                        ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"),
                        label="Open article toolbar actions",
                        tooltip="More actions",
                    )
                    with topbar_menu:
                        ui.menu_item("Share learning item", on_share)
    return ArticlesTopbarControls(search_input=search_input, sort_filter=sort_filter, meta=meta)


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
    with ui.expansion("More filters").props("dense"):
        with ui.column().classes("w-full"):
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


def render_article_card(
    *,
    article_row: dict[str, Any],
    is_new: bool,
    tags: list[str],
    summary_text: str,
    subtitle_text: str,
    thumbnail_url: str,
    view_action: Any,
    review_action: Any,
    compact_mode: bool = False,
) -> None:
    """Render one article card with actions."""
    title = str(article_row.get("title") or "").strip()
    url = str(article_row.get("url") or "").strip()
    subtitle_parts = [part.strip() for part in str(subtitle_text or "").split("·") if str(part).strip()]

    with ui.card().classes("w-full lp-card lp-card--hover lp-article-card"):
        _render_article_topright(is_new=is_new, review_action=review_action)
        with render_card_main_row(classes="lp-article-card-main"):
            _render_article_card_content(
                title=title,
                url=url,
                tags=tags,
                summary_text=summary_text,
                subtitle_parts=subtitle_parts,
                view_action=view_action,
                compact_mode=compact_mode,
            )
            _render_article_thumbnail(thumbnail_url=thumbnail_url)


def _render_article_topright(*, is_new: bool, review_action: Any) -> None:
    """Render card top-right status and menu controls."""
    with render_card_topright():
        if is_new:
            ui.label("New").classes("lp-chip lp-chip--sky")
        card_menu = apply_icon_button_a11y(
            ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"),
            label="Open article actions",
            tooltip="Article actions",
        )
        with card_menu:
            ui.menu_item("Review", review_action)


def _render_article_card_content(
    *,
    title: str,
    url: str,
    tags: list[str],
    summary_text: str,
    subtitle_parts: list[str],
    view_action: Any,
    compact_mode: bool,
) -> None:
    """Render article card text and actions."""
    with render_card_content_column(classes="lp-article-card-content"):
        ui.label(title).classes("text-lg font-semibold lp-card-title")
        if url and (not compact_mode):
            ui.link(url, url).props("target=_blank").classes("text-sm")

        _render_article_meta(subtitle_parts=subtitle_parts, url=url, compact_mode=compact_mode)
        _render_article_tags(tags=tags)
        if compact_mode:
            ui.element("div").classes("lp-card-meta-spacer")
        _render_article_review_summary(summary_text=summary_text)

        def _render_actions() -> None:
            ui.button("Open details", on_click=view_action).props("dense")

        render_card_actions_row(render_actions=_render_actions)


def _render_article_meta(*, subtitle_parts: list[str], url: str, compact_mode: bool) -> None:
    """Render article byline/date context."""
    with ui.row().classes("items-center gap-2 flex-wrap lp-article-meta-row"):
        ui.label("Article").classes("lp-meta-chip lp-meta-chip--quiet")
        if subtitle_parts:
            ui.label(subtitle_parts[0]).classes("text-xs lp-card-subtitle lp-article-byline")
        if len(subtitle_parts) > 1:
            ui.label(subtitle_parts[1]).classes("text-xs lp-card-subtitle lp-article-date")
    if not compact_mode:
        return

    context_line = subtitle_parts[1] if len(subtitle_parts) > 1 else ""
    if not context_line and url:
        context_line = "Source link"
    ui.label(context_line or "Shared by teammate").classes("text-xs lp-card-subtitle lp-article-context-line")


def _render_article_tags(*, tags: list[str]) -> None:
    """Render article tag chips."""
    with ui.row().classes("items-center gap-2 flex-wrap mt-1 lp-article-tag-row"):
        if not tags:
            ui.label("").classes("lp-article-tag-placeholder")
            return
        for tag in tags[:10]:
            ui.label(tag).classes("lp-meta-chip")
        if len(tags) > 10:
            ui.label(f"+{len(tags) - 10}").classes("lp-meta-chip")


def _render_article_review_summary(*, summary_text: str) -> None:
    """Render article review summary line."""
    summary = str(summary_text or "").strip()
    review_classes = "lp-card-review-line lp-article-summary-chip"
    if not summary:
        review_classes += " lp-card-review-line--empty"
    ui.label(summary or "No reviews yet").classes(review_classes)


def _render_article_thumbnail(*, thumbnail_url: str) -> None:
    """Render article thumbnail or fallback icon."""
    with ui.element("div").classes("lp-article-media-slot"):
        safe_src = html.escape(str(thumbnail_url or "").strip(), quote=True)
        if safe_src:
            ui.html(
                (
                    '<img class="lp-course-thumb lp-course-thumb--side lp-article-thumb" '
                    f'src="{safe_src}" '
                    'alt="Article thumbnail" loading="lazy" referrerpolicy="no-referrer">'
                ),
                sanitize=False,
            )
            return
        with ui.element("div").classes("lp-course-thumb lp-course-thumb--side lp-course-thumb--placeholder-block"):
            ui.icon("article").classes("lp-course-thumb-placeholder-block-icon")


def render_articles_catalog(
    *,
    shown_page: list[dict[str, Any]],
    total_count: int,
    render_article_item: Any,
    on_load_more: Any,
) -> None:
    """Render article cards for the current page and an optional load-more footer."""
    for article in list(shown_page or []):
        render_article_item(article)

    if int(total_count) <= len(list(shown_page or [])):
        return

    render_load_more_footer(
        shown_page_count=len(list(shown_page or [])),
        shown_total_count=int(total_count),
        on_load_more=on_load_more,
    )
