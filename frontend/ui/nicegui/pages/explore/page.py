"""Explore page with unified discovery across courses and articles."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.catalog_hero import render_catalog_hero
from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.detail_page import (
    render_explore_article_detail_page,
    render_explore_course_detail_page,
    render_explore_path_detail_page,
    render_explore_video_detail_page,
)
from frontend.ui.nicegui.pages.explore.event_bindings import bind_refresh_events
from frontend.ui.nicegui.pages.explore.list_flow import build_sections_deps, ExploreSectionsUiControls
from frontend.ui.nicegui.pages.explore.list_sections import (
    render_explore_empty_state,
    render_explore_sections,
)
from frontend.ui.nicegui.pages.explore.mutations_flow import build_mutation_handlers
from frontend.ui.nicegui.pages.explore.sections import (
    ExploreFilterControls,
    render_explore_filters_dialog,
    render_explore_share_dialog,
    render_explore_topbar,
)
from frontend.ui.nicegui.pages.explore.share_flow import create_explore_share_bindings
from frontend.ui.nicegui.pages.explore.state import ExplorePageState, ExploreUiFlags
from frontend.ui.nicegui.pages.explore.ui_glue import (
    apply_explore_filter_options,
    clear_explore_filter_controls,
    normalize_sort,
    normalize_tab,
    should_emit_first_search,
)
from frontend.ui.nicegui.pages.explore.view_model import build_explore_visible_results, ExploreListFilters


async def _render_explore_page(*, store: SessionStore, api: ApiClient) -> None:
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    is_admin = str(user.get("role") or "") == "admin"

    controller = ExplorePageController(api=api)

    render_shell(title="Explore", store=store, api=api)

    request = getattr(ui.context.client, "request", None)
    query_params = getattr(request, "query_params", None)
    initial_tab = normalize_tab((query_params or {}).get("tab", "all") if query_params is not None else "all")

    state = ExplorePageState()
    ui_flags = ExploreUiFlags()

    with render_catalog_scope(variant="explore").classes("lp-container"):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        render_catalog_hero(
            eyebrow="",
            title="Find the next course, video, path, or article worth sharing",
            subtitle="Search broadly, then narrow by scope and filters to move from browse to action quickly.",
        )
        # Sticky topbar uses a negative top margin; reserve vertical space so it
        # doesn't visually overlap this subtitle line.
        ui.element("div").classes("h-3")

        filter_controls: ExploreFilterControls | None = None

        def _reset_filters() -> None:
            assert filter_controls is not None
            clear_explore_filter_controls(controls=filter_controls)
            list_view.refresh()

        def _refresh_filter_options() -> None:
            assert filter_controls is not None
            apply_explore_filter_options(
                controls=filter_controls,
                courses=list(state.courses or []),
                videos=list(state.videos or []),
                articles=list(state.articles or []),
            )

        @guard_ui_action(title="Load explore failed")
        async def _load() -> None:
            await controller.load(
                state=state,
                refresh_ui=list_view.refresh,
                refresh_filter_options=_refresh_filter_options,
                notify_articles_warning=lambda message: safe_notify(
                    f"Articles unavailable in Explore ({message})",
                    type="warning",
                ),
                notify_videos_warning=lambda message: safe_notify(
                    f"Videos unavailable in Explore ({message})",
                    type="warning",
                ),
                notify_paths_warning=lambda message: safe_notify(
                    f"Paths unavailable in Explore ({message})",
                    type="warning",
                ),
            )

        share_bindings = create_explore_share_bindings(
            on_open_learning_item_share_page=lambda: ui.navigate.to("/share/item"),
            on_open_path_share_page=lambda: ui.navigate.to("/share/path"),
            on_unknown_target=lambda tab: ui.navigate.to("/explore?tab=" + {"path": "paths"}.get(tab, "courses")),
        )
        share_dialog = render_explore_share_dialog(
            on_share_learning_item=lambda: share_bindings.open_share_target("learning_item"),
            on_share_path=lambda: share_bindings.open_share_target("path"),
        )

        topbar = render_explore_topbar(
            initial_tab=initial_tab,
            on_open_share=share_dialog.open,
        )
        filter_controls = render_explore_filters_dialog(on_reset=_reset_filters)

        mutation_handlers = build_mutation_handlers(
            controller=controller,
            state=state,
            refresh_ui=lambda: list_view.refresh(),
        )

        def _show_more_learning_items() -> None:
            ui_flags.learning_items_visible_limit = int(ui_flags.learning_items_visible_limit or 8) + 8
            list_view.refresh()

        @ui.refreshable
        def list_view() -> None:
            tab_value = normalize_tab(topbar.tab_filter.value)
            sort_value = normalize_sort(topbar.sort_filter.value)
            assert filter_controls is not None

            if state.loading and not state.loaded_once:
                with ui.column().classes("w-full gap-3"):
                    render_card_skeletons(count=4)
                return

            results = build_explore_visible_results(
                state=state,
                filters=ExploreListFilters(
                    tab=tab_value,
                    sort=sort_value,
                    needle=str(topbar.search_input.value or "").strip(),
                    provider=str(filter_controls.provider_filter.value or ""),
                    category=str(filter_controls.category_filter.value or ""),
                    tag=str(filter_controls.tag_filter.value or ""),
                    author=str(filter_controls.author_filter.value or ""),
                ),
            )
            topbar.meta.text = results.meta_text

            with ui.element("div").classes("w-full lp-refresh-region"):
                if (
                    not results.shown_courses
                    and not results.shown_videos
                    and not results.shown_paths
                    and not results.shown_articles
                ):
                    render_explore_empty_state(
                        loaded_once=state.loaded_once,
                        on_refresh=_load,
                        on_reset_filters=_reset_filters,
                    )
                    return

                render_explore_sections(
                    shown_courses=results.shown_courses,
                    shown_paths=results.shown_paths,
                    shown_learning_items=results.shown_learning_items,
                    deps=build_sections_deps(
                        state=state,
                        username=username,
                        is_admin=is_admin,
                        show_all_categories=bool(ui_flags.show_all_categories),
                        controller=controller,
                        on_set_tracking=mutation_handlers.set_tracking,
                        on_clear_tracking=mutation_handlers.clear_tracking,
                        on_toggle_path_selection=mutation_handlers.toggle_path_selection,
                        on_open_path=lambda path_id: ui.navigate.to(f"/explore/paths/{int(path_id)}"),
                        ui_controls=ExploreSectionsUiControls(
                            learning_items_visible_limit=int(ui_flags.learning_items_visible_limit or 8),
                            on_show_more_learning_items=_show_more_learning_items,
                        ),
                    ),
                )

        def _on_search_change(*_args: Any) -> None:
            if should_emit_first_search(
                search_value=str(topbar.search_input.value or ""),
                telemetry_emitted=ui_flags.search_telemetry_emitted,
            ):
                ui_flags.search_telemetry_emitted = True
                track_ui_event_nowait(api=api, event_name="first_search", context={"page": "explore"})
            list_view.refresh()

        bind_refresh_events(
            topbar=topbar,
            filter_controls=filter_controls,
            on_search_change=_on_search_change,
            on_refresh=lambda: list_view.refresh(),
        )

        list_view()
        await _load()
        list_view.refresh()


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/explore` route."""

    @ui.page("/explore")
    async def explore_page() -> None:
        await _render_explore_page(store=store, api=api)

    @ui.page("/explore/courses/{course_id}")
    async def explore_course_detail_page(course_id: str) -> None:
        await render_explore_course_detail_page(store=store, api=api, course_id=course_id)

    @ui.page("/explore/paths/{path_id}")
    async def explore_path_detail_page(path_id: str) -> None:
        await render_explore_path_detail_page(store=store, api=api, path_id=path_id)

    @ui.page("/explore/articles/{article_id}")
    async def explore_article_detail_page(article_id: str) -> None:
        await render_explore_article_detail_page(store=store, api=api, article_id=article_id)

    @ui.page("/explore/videos/{video_id}")
    async def explore_video_detail_page(video_id: str) -> None:
        await render_explore_video_detail_page(store=store, api=api, video_id=video_id)
