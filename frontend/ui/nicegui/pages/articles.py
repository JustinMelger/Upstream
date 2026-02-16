"""Articles (shared links) page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import format_date
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.articles_service import (
    article_is_new,
    build_facet_counts,
    filter_articles,
    load_articles,
    parse_tags,
    sort_articles,
)


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/articles` route."""

    @ui.page("/articles")
    async def articles_page() -> None:
        if await require_user(store, api) is None:
            return

        render_shell(title="Articles", store=store, api=api)

        articles: list[dict[str, Any]] = []
        loading = False
        loaded_once = False
        page_size = 10
        visible_count = page_size

        tag_filter: Any = None
        author_filter: Any = None
        sort_filter: Any = None
        refresh_btn: Any = None
        meta: Any = None

        # Share dialog (pre-built so opening is instant).
        share_dialog = ui.dialog()
        with share_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
            ui.label("Share article").classes("text-xl font-semibold")
            new_title = ui.input("Title").props("clearable").classes("w-full")
            new_url = ui.input("URL").props("clearable").classes("w-full")
            new_tags = ui.input("Tags (comma separated)").props("clearable").classes("w-full")
            with ui.row().classes("justify-end mt-4"):

                @guard_ui_action(title="Share failed")
                async def _submit_share() -> None:
                    payload = {
                        "title": str(new_title.value or ""),
                        "url": str(new_url.value or ""),
                        "tags": str(new_tags.value or ""),
                    }
                    await api.post("/articles", payload)
                    ui.notify("Shared", type="positive")
                    share_dialog.close()
                    await _load()

                ui.button("Share", on_click=_submit_share)
                ui.button("Cancel", on_click=share_dialog.close).props("outline")

        def _open_share_dialog() -> None:
            new_title.value = ""
            new_url.value = ""
            new_tags.value = ""
            share_dialog.open()

        def _recompute_facets(*, needle: str) -> None:
            if tag_filter is None or author_filter is None:
                return

            tag_v = str(tag_filter.value or "")
            author_v = str(author_filter.value or "")

            # Compute counts as if the current facet value was not applied, so
            # switching options feels predictable.
            tag_counts, author_counts = build_facet_counts(articles, needle=needle, tag="", author=author_v)
            _, author_counts_for_any_tag = build_facet_counts(articles, needle=needle, tag=tag_v, author="")

            tag_filter.options = {"": "Any tag"} | {
                t: f"{t} ({tag_counts[t]})" for t in sorted(tag_counts.keys(), key=lambda x: x.lower())
            }
            author_filter.options = {"": "Anyone"} | {
                a: f"{a} ({author_counts_for_any_tag[a]})"
                for a in sorted(author_counts_for_any_tag.keys(), key=lambda x: x.lower())
            }

            if tag_filter.value and tag_filter.value not in tag_filter.options:
                tag_filter.value = ""
            if author_filter.value and author_filter.value not in author_filter.options:
                author_filter.value = ""

            tag_filter.update()
            author_filter.update()

        def _refresh_list(*_: Any) -> None:
            nonlocal visible_count
            visible_count = page_size
            needle = str(q.value or "").strip()
            _recompute_facets(needle=needle)
            active_filters.refresh()
            articles_list.refresh()

        def _reset_filters() -> None:
            nonlocal visible_count
            visible_count = page_size
            q.value = ""
            q.update()
            if tag_filter is not None:
                tag_filter.value = ""
                tag_filter.update()
            if author_filter is not None:
                author_filter.value = ""
                author_filter.update()
            if sort_filter is not None:
                sort_filter.value = ""
                sort_filter.update()
            _recompute_facets(needle="")
            active_filters.refresh()
            articles_list.refresh()

        @guard_ui_action(title="Load failed")
        async def _load() -> None:
            nonlocal articles, loading, loaded_once, visible_count
            if loading:
                return
            loading = True
            visible_count = page_size
            refresh_btn.disable()
            meta.text = "Loading..."
            articles_list.refresh()
            try:
                articles = list(await load_articles(api=api) or [])
                loaded_once = True
                needle = str(q.value or "").strip()
                _recompute_facets(needle=needle)
                meta.text = f"{len(articles)} articles"
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                articles = []
                loaded_once = True
                meta.text = "Failed to load"
            finally:
                loading = False
                refresh_btn.enable()
                active_filters.refresh()
                articles_list.refresh()

        with render_container():
            with ui.row().classes("lp-topbar"):
                q = ui.input("Search articles").props("clearable debounce=300").style("flex: 1")
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    ui.button("Share", on_click=_open_share_dialog).props("dense")
                    sort_filter = (
                        ui.select(
                            {
                                "": "Recommended",
                                "newest": "Newest",
                                "title_az": "Title A–Z",
                                "author_az": "Author A–Z",
                            },
                            value="",
                            label=None,
                        )
                        .props("dense")
                        .style("min-width: 180px")
                    )
                    meta = ui.label("").classes("lp-topbar-meta")

            def _render_rail() -> None:
                nonlocal tag_filter, author_filter, refresh_btn

                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("Filters").classes("text-md font-semibold")
                    refresh_btn = ui.button("Refresh", on_click=_load).props("outline dense")

                ui.label("Tip: share useful resources with colleagues.").classes("text-xs").style("color: var(--lp-muted)")

                tag_filter = ui.select({"": "Any tag"}, label="Tag", value="").props("dense").classes("w-full")
                author_filter = ui.select({"": "Anyone"}, label="Shared by", value="").props("dense").classes("w-full")

                ui.button("Reset all", on_click=_reset_filters).props("outline").classes("w-full mt-2")

            @ui.refreshable
            def active_filters() -> None:
                any_chip = False

                def _chip(label: str, on_clear: Any) -> None:
                    with ui.element("div").classes("lp-filter-chip"):
                        ui.label(label)
                        ui.button("×", on_click=on_clear).props("dense flat")

                with ui.row().classes("items-center gap-2 w-full flex-wrap"):
                    if str(q.value or "").strip():
                        any_chip = True

                        def _clear_q() -> None:
                            q.value = ""
                            q.update()
                            _refresh_list()

                        _chip(f"Search: {str(q.value or '').strip()}", _clear_q)

                    if tag_filter is not None and str(tag_filter.value or "").strip():
                        any_chip = True
                        t = str(tag_filter.value or "").strip()

                        def _clear_tag() -> None:
                            tag_filter.value = ""
                            tag_filter.update()
                            _refresh_list()

                        _chip(f"Tag: {t}", _clear_tag)

                    if author_filter is not None and str(author_filter.value or "").strip():
                        any_chip = True
                        a = str(author_filter.value or "").strip()

                        def _clear_author() -> None:
                            author_filter.value = ""
                            author_filter.update()
                            _refresh_list()

                        _chip(f"Shared by: {a}", _clear_author)

                    if sort_filter is not None and str(sort_filter.value or "").strip():
                        any_chip = True
                        sv = str(sort_filter.value or "").strip()
                        label = str(sort_filter.options.get(sv) or sv)

                        def _clear_sort() -> None:
                            sort_filter.value = ""
                            sort_filter.update()
                            _refresh_list()

                        _chip(f"Sort: {label}", _clear_sort)

                if not any_chip:
                    return

            @ui.refreshable
            def articles_list() -> None:
                nonlocal visible_count
                needle = str(q.value or "")
                tag_v = str(tag_filter.value or "") if tag_filter is not None else ""
                author_v = str(author_filter.value or "") if author_filter is not None else ""
                sort_v = str(sort_filter.value or "") if sort_filter is not None else ""

                shown = filter_articles(articles, needle=needle, tag=tag_v, author=author_v)
                shown = sort_articles(shown, sort_key=sort_v)

                with ui.column().classes("w-full gap-3"):
                    if loading or not loaded_once:
                        render_card_skeletons(count=3)
                        return

                    if not shown:
                        any_filters = any([str(q.value or "").strip(), tag_v.strip(), author_v.strip()])
                        if not articles and not any_filters:
                            ui.label("No articles yet.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.label("Share the first link to get started.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.button("Share an article", on_click=_open_share_dialog).props("outline")
                            return
                        ui.label("No articles match your filters.").classes("text-sm").style("color: var(--lp-muted)")
                        with ui.row().classes("items-center gap-2"):
                            ui.button("Reset all", on_click=_reset_filters).props("outline")
                            ui.button("Refresh", on_click=_load).props("outline")
                        return

                    total = len(shown)
                    shown_page = shown[: max(0, int(visible_count))]

                    for a in shown_page:
                        title = str(a.get("title") or "").strip()
                        url = str(a.get("url") or "").strip()
                        created_by = str(a.get("created_by") or "").strip()
                        created_at = str(a.get("created_at") or "").strip()

                        with ui.card().classes("w-full lp-card lp-card--hover"):
                            with ui.element("div").classes("lp-card-topright"):
                                if article_is_new(a):
                                    ui.label("New").classes("lp-chip lp-chip--sky")

                            ui.label(title).classes("text-lg font-semibold")
                            if url:
                                ui.link(url, url).props("target=_blank").classes("text-sm")

                            subtitle_bits = [
                                f"Shared by {created_by}" if created_by else "",
                                format_date(created_at),
                            ]
                            ui.label(" · ".join([b for b in subtitle_bits if b])).classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )

                            tags = parse_tags(str(a.get("tags") or ""))
                            if tags:
                                with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                                    for t in tags[:10]:
                                        ui.label(t).classes("lp-meta-chip")
                                    if len(tags) > 10:
                                        ui.label(f"+{len(tags) - 10}").classes("lp-meta-chip")

                            if url:
                                with ui.row().classes("items-center gap-2 mt-2"):

                                    def _open(*, _url: str = url) -> None:
                                        ui.navigate.to(_url, new_tab=True)

                                    def _copy_btn(*, _url: str = url) -> None:
                                        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(_url)});")
                                        ui.notify("Link copied", type="positive")

                                    ui.button("", icon="open_in_new", on_click=_open).props("outline dense").tooltip("Open")
                                    ui.button("", icon="content_copy", on_click=_copy_btn).props("outline dense").tooltip(
                                        "Copy link"
                                    )

                    if total > len(shown_page):
                        with ui.row().classes("items-center justify-center mt-2"):

                            def _load_more() -> None:
                                nonlocal visible_count
                                visible_count = min(total, int(visible_count) + page_size)
                                articles_list.refresh()

                            ui.button(f"Load more ({len(shown_page)}/{total})", on_click=_load_more).props("outline")

            def _render_main() -> None:
                active_filters()
                articles_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            q.on("update:model-value", _refresh_list)
            sort_filter.on("update:model-value", _refresh_list)
            if tag_filter is not None:
                tag_filter.on("update:model-value", _refresh_list)
            if author_filter is not None:
                author_filter.on("update:model-value", _refresh_list)

            await _load()
