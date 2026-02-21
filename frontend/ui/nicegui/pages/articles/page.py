"""Articles (shared links) page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.catalog_hero import render_catalog_hero
from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.articles.actions import (
    build_article_card_actions,
    build_articles_facet_controls,
    clear_article_filter_and_refresh,
    recompute_article_facet_controls_for_search,
)
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.articles.detail_flow import open_article_details_flow
from frontend.ui.nicegui.pages.articles.dialogs import build_share_article_dialog
from frontend.ui.nicegui.pages.articles.filters import normalize_articles_filter_values
from frontend.ui.nicegui.pages.articles.orchestration import (
    clear_articles_filter_values,
    load_articles_page,
    perform_create_article,
    refresh_articles_list,
)
from frontend.ui.nicegui.pages.articles.reducers import derive_shown_articles
from frontend.ui.nicegui.pages.articles.sections import (
    render_active_filter_chips,
    render_article_card,
    render_articles_catalog,
    render_articles_empty_state,
    render_articles_topbar,
    render_filters_rail,
)
from frontend.ui.nicegui.pages.articles.state import ArticlesPageState
from frontend.ui.nicegui.pages.articles.ui_glue import (
    build_active_filter_chips,
    compute_articles_meta_text,
    compute_expanded_visible_count,
)
from frontend.ui.nicegui.pages.articles.view_model import map_article_card_view


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
            await perform_create_article(
                payload=payload,
                controller=controller,
                reload_page=_load,
            )

        _open_share_dialog = build_share_article_dialog(on_submit=_submit_share)

        def _facet_controls() -> Any:
            return build_articles_facet_controls(
                search_input=q,
                tag_filter=tag_filter,
                author_filter=author_filter,
                sort_filter=sort_filter,
            )

        def _refresh_list(*_: Any) -> None:
            refresh_articles_list(
                state=state,
                recompute_facets=lambda: recompute_article_facet_controls_for_search(
                    controls=_facet_controls(),
                    articles=state.articles,
                    search_value=str(q.value or "").strip(),
                ),
                refresh_active_filters=active_filters.refresh,
                refresh_articles_list_ui=articles_list.refresh,
            )

        def _reset_filters() -> None:
            clear_articles_filter_values(
                state=state,
                controls=_facet_controls(),
                recompute_facets=lambda: recompute_article_facet_controls_for_search(
                    controls=_facet_controls(),
                    articles=state.articles,
                    search_value="",
                ),
                refresh_active_filters=active_filters.refresh,
                refresh_articles_list_ui=articles_list.refresh,
            )

        @guard_ui_action(title="Load failed")
        async def _load() -> None:
            await load_articles_page(
                state=state,
                controller=controller,
                refresh_btn=refresh_btn,
                meta=meta,
                recompute_facets=lambda: recompute_article_facet_controls_for_search(
                    controls=_facet_controls(),
                    articles=state.articles,
                    search_value=str(q.value or "").strip(),
                ),
                refresh_active_filters=active_filters.refresh,
                refresh_articles_list_ui=articles_list.refresh,
                notify_error=lambda message: safe_notify(message, type="negative"),
                compute_meta_text=compute_articles_meta_text,
            )

        @guard_ui_action(title="Load article details failed")
        async def _open_details(article: dict[str, Any], *, focus_reviews: bool = False) -> None:
            await open_article_details_flow(
                article=article,
                focus_reviews=focus_reviews,
                username=username,
                is_admin=is_admin,
                controller=controller,
                state=state,
            )

        with render_catalog_scope(variant="articles").classes("lp-container"):
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

                render_active_filter_chips(
                    chips=chips,
                    on_clear_key=lambda key: clear_article_filter_and_refresh(
                        key=str(key),
                        controls=_facet_controls(),
                        refresh_list=_refresh_list,
                    ),
                )

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

                    with ui.column().classes("w-full gap-1 lp-courses-section"):
                        ui.label("Latest reads").classes("lp-courses-section-title")
                        ui.label("Shared resources from your team").classes("lp-courses-section-subtitle")

                    total = len(shown)
                    shown_page = shown[: max(0, int(state.visible_count))]

                    def _render_article_item(article_row: dict[str, Any]) -> None:
                        article_id = int(article_row.get("id") or 0)
                        card_vm = map_article_card_view(
                            article_row=article_row,
                            review_summary_row=state.review_summary_by_article_id.get(article_id),
                        )
                        actions = build_article_card_actions(
                            article_row=article_row,
                            on_open_details=lambda _a, _focus: _open_details(_a, focus_reviews=bool(_focus)),
                        )
                        render_article_card(
                            article_row=article_row,
                            is_new=card_vm.is_new,
                            tags=card_vm.tags,
                            summary_text=card_vm.summary_text,
                            subtitle_text=card_vm.subtitle_text,
                            view_action=actions.on_view,
                            review_action=actions.on_review,
                        )

                    def _load_more() -> None:
                        state.visible_count = compute_expanded_visible_count(
                            current_visible=int(state.visible_count),
                            total_count=total,
                            page_size=state.page_size,
                        )
                        articles_list.refresh()

                    render_articles_catalog(
                        shown_page=shown_page,
                        total_count=total,
                        render_article_item=_render_article_item,
                        on_load_more=_load_more,
                    )

            def _render_main() -> None:
                render_catalog_hero(
                    eyebrow="Editorial stream",
                    title="Read what your team is sharing now",
                    subtitle="Scan trusted links fast, then open details when you want deeper context.",
                )
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
