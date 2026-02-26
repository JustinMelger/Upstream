"""Explore page with unified discovery across courses and articles."""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation_intents import set_catalog_share_storage_intent
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.articles.reducers import derive_shown_articles
from frontend.ui.nicegui.pages.courses.reducers import filter_courses, sort_courses
from frontend.ui.nicegui.pages.explore.actions import build_explore_course_actions, open_explore_article_details
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.detail_page import (
    render_explore_article_detail_page,
    render_explore_course_detail_page,
    render_explore_path_detail_page,
)
from frontend.ui.nicegui.pages.explore.list_sections import (
    ExploreSectionsDeps,
    render_explore_empty_state,
    render_explore_sections,
)
from frontend.ui.nicegui.pages.explore.sections import (
    ExploreFilterControls,
    render_explore_filters_dialog,
    render_explore_share_dialog,
    render_explore_topbar,
)
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.explore.ui_glue import (
    apply_explore_filter_options,
    apply_tab_scope,
    clear_explore_filter_controls,
    compute_explore_meta_text,
    normalize_sort,
    normalize_tab,
)
from frontend.ui.nicegui.pages.paths.reducers import filter_paths_by_needle, sort_paths


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
    flags = {"search_telemetry_emitted": False, "show_all_categories": False}

    with render_catalog_scope(variant="explore").classes("lp-container"):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        # Sticky topbar uses a negative top margin; reserve vertical space so it
        # doesn't visually overlap this subtitle line.
        ui.element("div").classes("h-3")

        def _open_manage_share(target: str) -> None:
            set_catalog_share_storage_intent(storage_user=app.storage.user, target=str(target))
            if str(target) == "course":
                ui.navigate.to("/manage/courses")
                return
            if str(target) == "path":
                ui.navigate.to("/manage/paths")
                return
            ui.navigate.to("/manage/articles")

        share_dialog = render_explore_share_dialog(
            on_share_course=lambda: _open_manage_share("course"),
            on_share_path=lambda: _open_manage_share("path"),
            on_share_article=lambda: _open_manage_share("article"),
        )

        filter_controls: ExploreFilterControls | None = None

        def _reset_filters() -> None:
            assert filter_controls is not None
            clear_explore_filter_controls(controls=filter_controls)
            list_view.refresh()

        topbar = render_explore_topbar(
            initial_tab=initial_tab,
            on_open_filters=lambda: filter_controls.dialog.open() if filter_controls is not None else None,
            on_open_share=share_dialog.open,
        )
        categories_btn = ui.button("More categories").props("outline dense")
        filter_controls = render_explore_filters_dialog(on_reset=_reset_filters)

        def _toggle_categories() -> None:
            flags["show_all_categories"] = not bool(flags["show_all_categories"])
            categories_btn.text = "Fewer categories" if flags["show_all_categories"] else "More categories"
            categories_btn.update()
            list_view.refresh()

        categories_btn.on("click", lambda *_: _toggle_categories())

        def _refresh_meta(*, course_count: int, path_count: int, article_count: int, tab_value: str) -> None:
            topbar.meta.text = compute_explore_meta_text(
                tab_value=tab_value,
                course_count=course_count,
                path_count=path_count,
                article_count=article_count,
            )

        def _refresh_filter_options() -> None:
            assert filter_controls is not None
            apply_explore_filter_options(
                controls=filter_controls,
                courses=list(state.courses or []),
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
                notify_paths_warning=lambda message: safe_notify(
                    f"Paths unavailable in Explore ({message})",
                    type="warning",
                ),
            )

        async def _set_tracking(course_id: int, status: str) -> None:
            await controller.set_tracking_status(
                state=state,
                course_id=int(course_id),
                status=str(status),
                refresh_ui=list_view.refresh,
            )

        async def _clear_tracking(course_id: int) -> None:
            await controller.clear_tracking_status(
                state=state,
                course_id=int(course_id),
                refresh_ui=list_view.refresh,
            )

        async def _toggle_path_selection(path_id: int) -> None:
            await controller.toggle_path_selection(
                state=state,
                path_id=int(path_id),
                refresh_ui=list_view.refresh,
            )

        @ui.refreshable
        def list_view() -> None:
            tab_value = normalize_tab(topbar.tab_filter.value)
            sort_value = normalize_sort(topbar.sort_filter.value)
            needle = str(topbar.search_input.value or "").strip()

            if state.loading and not state.loaded_once:
                with ui.column().classes("w-full gap-3"):
                    render_card_skeletons(count=4)
                return

            shown_courses = filter_courses(
                courses=list(state.courses or []),
                tracking_by_course_id=dict(state.tracking_by_course_id or {}),
                scope_value="all",
                needle=needle,
                provider_value=str(filter_controls.provider_filter.value or ""),
                category_value=str(filter_controls.category_filter.value or ""),
                level_value="",
                status_value="",
            )
            shown_courses = sort_courses(
                courses=shown_courses,
                sort_value=sort_value,
                review_summary_by_course_id=dict(state.course_review_summary_by_course_id or {}),
                parse_iso_datetime=parse_iso_datetime,
            )

            shown_articles = derive_shown_articles(
                articles=list(state.articles or []),
                needle=needle,
                tag_value=str(filter_controls.tag_filter.value or ""),
                author_value=str(filter_controls.author_filter.value or ""),
                sort_value=sort_value,
            )
            shown_paths = filter_paths_by_needle(list(state.paths or []), needle.lower())
            shown_paths = sort_paths(
                paths=shown_paths,
                sort_value=sort_value,
                path_review_summary_by_id=dict(state.path_review_summary_by_id or {}),
                parse_iso_datetime=parse_iso_datetime,
            )

            shown_courses, shown_paths, shown_articles = apply_tab_scope(
                tab_value=tab_value,
                shown_courses=shown_courses,
                shown_paths=shown_paths,
                shown_articles=shown_articles,
            )

            _refresh_meta(
                course_count=len(shown_courses),
                path_count=len(shown_paths),
                article_count=len(shown_articles),
                tab_value=tab_value,
            )

            if not shown_courses and not shown_paths and not shown_articles:
                render_explore_empty_state(
                    loaded_once=state.loaded_once,
                    on_refresh=_load,
                    on_reset_filters=_reset_filters,
                )
                return

            render_explore_sections(
                shown_courses=shown_courses,
                shown_paths=shown_paths,
                shown_articles=shown_articles,
                deps=ExploreSectionsDeps(
                    state=state,
                    username=username,
                    is_admin=is_admin,
                    show_all_categories=bool(flags["show_all_categories"]),
                    course_actions_builder=lambda course_row, course_id, course_url: build_explore_course_actions(
                        course_row=course_row,
                        course_id=course_id,
                        course_url=course_url,
                        username=username,
                        is_admin=is_admin,
                        state=state,
                        controller=controller,
                        on_set_tracking=_set_tracking,
                        on_clear_tracking=_clear_tracking,
                    ),
                    on_set_tracking=_set_tracking,
                    on_clear_tracking=_clear_tracking,
                    on_toggle_path_selection=_toggle_path_selection,
                    open_path_details_dialog=lambda path_row, card_vm: ui.navigate.to(
                        f"/explore/paths/{int(path_row.get('id') or 0)}"
                    ),
                    open_article_details=open_explore_article_details,
                ),
            )

        def _on_search_change(*_args: Any) -> None:
            if not bool(flags["search_telemetry_emitted"]) and str(topbar.search_input.value or "").strip():
                flags["search_telemetry_emitted"] = True
                track_ui_event_nowait(api=api, event_name="first_search", context={"page": "explore"})
            list_view.refresh()

        topbar.search_input.on("update:model-value", _on_search_change)
        topbar.tab_filter.on("update:model-value", lambda *_: list_view.refresh())
        topbar.sort_filter.on("update:model-value", lambda *_: list_view.refresh())

        for control in [
            filter_controls.provider_filter,
            filter_controls.category_filter,
            filter_controls.tag_filter,
            filter_controls.author_filter,
        ]:
            control.on("update:model-value", lambda *_: list_view.refresh())

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
