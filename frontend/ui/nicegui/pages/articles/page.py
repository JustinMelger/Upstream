"""Articles (shared links) page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import format_date
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.articles.actions import build_article_card_actions
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.articles.dialogs import build_share_article_dialog, open_article_details_dialog
from frontend.ui.nicegui.pages.articles.filters import normalize_articles_filter_values
from frontend.ui.nicegui.pages.articles.reducers import compute_facet_state, derive_shown_articles
from frontend.ui.nicegui.pages.articles.sections import (
    render_active_filter_chips,
    render_article_card,
    render_articles_empty_state,
    render_articles_topbar,
    render_filters_rail,
)
from frontend.ui.nicegui.pages.articles.state import ArticlesPageState
from frontend.ui.nicegui.pages.articles.transitions import (
    begin_articles_load,
    clear_articles_state_on_load_error,
    finalize_articles_load,
)
from frontend.ui.nicegui.pages.articles.ui_glue import (
    article_is_new,
    build_active_filter_chips,
    compute_articles_meta_text,
    compute_expanded_visible_count,
    parse_tags,
)


def _format_review_summary(row: dict[str, Any] | None) -> str:
    """Format a review summary row into a compact label."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    return f"{avg:.1f}/5 ({count})"


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/articles` route."""

    @ui.page("/articles")
    async def articles_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"
        controller = ArticlesPageController(api=api)

        render_shell(title="Articles", store=store, api=api)

        state = ArticlesPageState()

        tag_filter: Any = None
        author_filter: Any = None
        sort_filter: Any = None
        refresh_btn: Any = None
        meta: Any = None

        async def _submit_share(payload: dict[str, Any]) -> None:
            await controller.create_article(payload=payload)
            await _load()

        _open_share_dialog = build_share_article_dialog(on_submit=_submit_share)

        def _recompute_facets(*, needle: str) -> None:
            if tag_filter is None or author_filter is None:
                return

            normalized = normalize_articles_filter_values(
                search_value=needle,
                tag_value=str(tag_filter.value or ""),
                author_value=str(author_filter.value or ""),
                sort_value=str(sort_filter.value or "") if sort_filter is not None else "",
            )
            tag_options, author_options, next_tag, next_author = compute_facet_state(
                articles=state.articles,
                needle=normalized.search,
                selected_tag=normalized.tag,
                selected_author=normalized.author,
            )
            tag_filter.options = tag_options
            author_filter.options = author_options
            tag_filter.value = next_tag
            author_filter.value = next_author

            tag_filter.update()
            author_filter.update()

        def _refresh_list(*_: Any) -> None:
            state.visible_count = state.page_size
            needle = str(q.value or "").strip()
            _recompute_facets(needle=needle)
            active_filters.refresh()
            articles_list.refresh()

        def _reset_filters() -> None:
            state.visible_count = state.page_size
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
            if state.loading:
                return
            load_start = begin_articles_load(page_size=state.page_size)
            state.loading = load_start.loading
            state.visible_count = load_start.visible_count
            refresh_btn.disable()
            meta.text = load_start.meta_text
            articles_list.refresh()
            ok = False
            try:
                bundle = await controller.load_list_bundle()
                state.articles = list(bundle.articles or [])
                state.review_summary_by_article_id = dict(bundle.review_summary_by_article_id or {})
                needle = str(q.value or "").strip()
                _recompute_facets(needle=needle)
                ok = True
            except ApiError as exc:
                safe_notify(str(exc), type="negative")
                clear_articles_state_on_load_error(state=state)
                needle = str(q.value or "").strip()
                _recompute_facets(needle=needle)
            finally:
                load_done = finalize_articles_load(ok=ok, article_count=len(state.articles))
                state.loading = load_done.loading
                state.loaded_once = load_done.loaded_once
                meta.text = compute_articles_meta_text(article_count=len(state.articles))
                refresh_btn.enable()
                active_filters.refresh()
                articles_list.refresh()

        @guard_ui_action(title="Load article details failed")
        async def _open_details(article: dict[str, Any], *, focus_reviews: bool = False) -> None:
            await open_article_details_dialog(
                article=article,
                focus_reviews=focus_reviews,
                username=username,
                is_admin=is_admin,
                load_reviews=lambda _article_id: controller.load_article_reviews(article_id=int(_article_id)),
                save_review=lambda _article_id, _rating, _text: controller.save_article_review(
                    article_id=int(_article_id),
                    rating=int(_rating),
                    text=str(_text or ""),
                ),
                delete_review=lambda _article_id, _review_id: controller.delete_article_review(
                    article_id=int(_article_id),
                    review_id=int(_review_id),
                ),
                review_summary_by_article_id=state.review_summary_by_article_id,
                format_review_summary=_format_review_summary,
                format_date=format_date,
            )

        with render_container():
            topbar = render_articles_topbar(on_share=_open_share_dialog)
            q = topbar.search_input
            sort_filter = topbar.sort_filter
            meta = topbar.meta

            def _render_rail() -> None:
                nonlocal tag_filter, author_filter, refresh_btn
                controls = render_filters_rail(
                    on_refresh=_load,
                    on_reset=_reset_filters,
                )
                tag_filter = controls.tag_filter
                author_filter = controls.author_filter
                refresh_btn = controls.refresh_btn

            @ui.refreshable
            def active_filters() -> None:
                chips = build_active_filter_chips(
                    search_value=str(q.value or ""),
                    tag_value=str(tag_filter.value or "") if tag_filter is not None else "",
                    author_value=str(author_filter.value or "") if author_filter is not None else "",
                    sort_value=str(sort_filter.value or "") if sort_filter is not None else "",
                    sort_options={str(k): str(v) for k, v in dict((sort_filter.options or {}) if sort_filter else {}).items()},
                )
                if not chips:
                    return

                def _clear_filter_key(key: str) -> None:
                    clear_map = {
                        "search": lambda: setattr(q, "value", "") or q.update(),
                        "tag": lambda: setattr(tag_filter, "value", "") or tag_filter.update(),
                        "author": lambda: setattr(author_filter, "value", "") or author_filter.update(),
                        "sort": lambda: setattr(sort_filter, "value", "") or sort_filter.update(),
                    }
                    clear = clear_map.get(str(key))
                    if callable(clear):
                        clear()
                    _refresh_list()

                render_active_filter_chips(chips=chips, on_clear_key=_clear_filter_key)

            @ui.refreshable
            def articles_list() -> None:
                normalized = normalize_articles_filter_values(
                    search_value=str(q.value or ""),
                    tag_value=str(tag_filter.value or "") if tag_filter is not None else "",
                    author_value=str(author_filter.value or "") if author_filter is not None else "",
                    sort_value=str(sort_filter.value or "") if sort_filter is not None else "",
                )

                shown = derive_shown_articles(
                    articles=state.articles,
                    needle=normalized.search,
                    tag_value=normalized.tag,
                    author_value=normalized.author,
                    sort_value=normalized.sort,
                )

                with ui.column().classes("w-full gap-3"):
                    if state.loading or not state.loaded_once:
                        render_card_skeletons(count=3)
                        return

                    if not shown:
                        any_filters = any([normalized.search, normalized.tag, normalized.author])
                        render_articles_empty_state(
                            has_articles=bool(state.articles),
                            any_filters=bool(any_filters),
                            on_share=_open_share_dialog,
                            on_reset=_reset_filters,
                            on_refresh=_load,
                        )
                        return

                    total = len(shown)
                    shown_page = shown[: max(0, int(state.visible_count))]

                    for a in shown_page:
                        created_by = str(a.get("created_by") or "").strip()
                        created_at = str(a.get("created_at") or "").strip()
                        summary = _format_review_summary(state.review_summary_by_article_id.get(int(a.get("id") or 0)))
                        subtitle_bits = [
                            f"Shared by {created_by}" if created_by else "",
                            format_date(created_at),
                        ]
                        actions = build_article_card_actions(
                            article_row=a,
                            on_open_details=lambda _a, _focus: _open_details(_a, focus_reviews=bool(_focus)),
                        )
                        render_article_card(
                            article_row=a,
                            is_new=bool(article_is_new(a)),
                            tags=parse_tags(str(a.get("tags") or "")),
                            summary_text=f"★ {summary}" if summary else "",
                            subtitle_text=" · ".join([b for b in subtitle_bits if b]),
                            view_action=actions.on_view,
                            review_action=actions.on_review,
                        )

                    if total > len(shown_page):

                        def _load_more() -> None:
                            state.visible_count = compute_expanded_visible_count(
                                current_visible=int(state.visible_count),
                                total_count=total,
                                page_size=state.page_size,
                            )
                            articles_list.refresh()

                        render_load_more_footer(
                            shown_page_count=len(shown_page),
                            shown_total_count=total,
                            on_load_more=_load_more,
                        )

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
