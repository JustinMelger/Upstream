"""Explore page with unified discovery across courses and articles."""

from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.path_card import render_path_card
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.articles.actions import build_article_card_actions
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.articles.reducers import derive_shown_articles
from frontend.ui.nicegui.pages.articles.sections import render_article_card
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.articles.view_model import map_article_card_view
from frontend.ui.nicegui.pages.courses.actions import build_course_card_actions
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.courses.reducers import filter_courses, sort_courses
from frontend.ui.nicegui.pages.courses.sections import render_course_card, render_courses_catalog
from frontend.ui.nicegui.pages.courses.ui_glue import resolve_tracking_status_value
from frontend.ui.nicegui.pages.courses.view_model import map_course_card_view
from frontend.ui.nicegui.pages.explore.orchestration import (
    clear_explore_tracking_status,
    load_explore_articles_background,
    load_explore_courses,
    load_explore_paths_background,
    set_explore_tracking_status,
)
from frontend.ui.nicegui.pages.explore.sections import (
    render_explore_article_rails,
    render_explore_filters_dialog,
    render_explore_topbar,
)
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.explore.ui_glue import compute_explore_meta_text, normalize_sort, normalize_tab
from frontend.ui.nicegui.pages.paths.actions import copy_path_link
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.reducers import filter_paths_by_needle, sort_paths
from frontend.ui.nicegui.pages.paths.state import PathsPageState
from frontend.ui.nicegui.pages.paths.view_model import map_path_card_view


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/explore` route."""

    @ui.page("/explore")
    async def explore_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"

        courses_controller = CoursesPageController(api=api)
        articles_controller = ArticlesPageController(api=api)
        paths_controller = PathsPageController(api=api)

        render_shell(title="Explore", store=store, api=api)

        request = getattr(ui.context.client, "request", None)
        query_params = getattr(request, "query_params", None)
        initial_tab = normalize_tab((query_params or {}).get("tab", "all") if query_params is not None else "all")

        state = ExplorePageState()

        with render_catalog_scope(variant="explore").classes("lp-container"):
            with ui.row().classes("w-full items-center"):
                ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
            # Sticky topbar uses a negative top margin; reserve vertical space so it
            # doesn't visually overlap this subtitle line.
            ui.element("div").classes("h-3")
            search_telemetry_emitted = False

            with ui.dialog() as share_dialog:
                with ui.card().classes("lp-card lp-dialog w-[min(540px,95vw)]"):
                    ui.label("Share with your team").classes("text-lg font-semibold")
                    ui.label("Choose what you want to share.").classes("text-sm").style("color: var(--lp-muted)")
                    with ui.column().classes("w-full gap-2 mt-2"):
                        ui.button(
                            "Share course", on_click=lambda: (share_dialog.close(), ui.navigate.to("/courses?share=1"))
                        ).props("unelevated")
                        ui.button(
                            "Share path", on_click=lambda: (share_dialog.close(), ui.navigate.to("/paths?share=1"))
                        ).props("outline")
                        ui.button(
                            "Share article",
                            on_click=lambda: (share_dialog.close(), ui.navigate.to("/articles?share=1")),
                        ).props("outline")
                    with ui.row().classes("justify-end w-full mt-1"):
                        ui.button("Cancel", on_click=share_dialog.close).props("flat")

            def _reset_filters() -> None:
                for control in [
                    filter_controls.provider_filter,
                    filter_controls.category_filter,
                    filter_controls.tag_filter,
                    filter_controls.author_filter,
                ]:
                    control.value = ""
                    control.update()
                list_view.refresh()

            topbar = render_explore_topbar(
                initial_tab=initial_tab,
                on_open_filters=lambda: filter_controls.dialog.open(),
                on_open_share=share_dialog.open,
            )
            filter_controls = render_explore_filters_dialog(on_reset=_reset_filters)

            def _refresh_meta(*, course_count: int, path_count: int, article_count: int, tab_value: str) -> None:
                topbar.meta.text = compute_explore_meta_text(
                    tab_value=tab_value,
                    course_count=course_count,
                    path_count=path_count,
                    article_count=article_count,
                )

            def _refresh_filter_options() -> None:
                provider_options = {"": "Any provider"}
                category_options = {"": "Any category"}
                for row in list(state.courses or []):
                    provider = str(row.get("provider") or "").strip()
                    category = str(row.get("category") or "").strip()
                    if provider and provider not in provider_options:
                        provider_options[provider] = provider
                    if category and category not in category_options:
                        category_options[category] = category

                tag_options = {"": "Any tag"}
                author_options = {"": "Anyone"}
                for row in list(state.articles or []):
                    author = str(row.get("created_by") or "").strip()
                    if author and author not in author_options:
                        author_options[author] = author
                    for tag in parse_tags(str(row.get("tags") or "")):
                        if tag and tag not in tag_options:
                            tag_options[tag] = tag

                filter_controls.provider_filter.options = provider_options
                filter_controls.provider_filter.update()
                filter_controls.category_filter.options = category_options
                filter_controls.category_filter.update()
                filter_controls.tag_filter.options = tag_options
                filter_controls.tag_filter.update()
                filter_controls.author_filter.options = author_options
                filter_controls.author_filter.update()

            async def _load_articles_background() -> None:
                await load_explore_articles_background(
                    state=state,
                    feature_articles_enabled=settings.feature_articles,
                    articles_controller=articles_controller,
                    refresh_ui=list_view.refresh,
                    refresh_filter_options=_refresh_filter_options,
                    notify_warning=lambda message: safe_notify(
                        f"Articles unavailable in Explore ({message})",
                        type="warning",
                    ),
                )

            async def _load_paths_background() -> None:
                await load_explore_paths_background(
                    state=state,
                    paths_controller=paths_controller,
                    refresh_ui=list_view.refresh,
                    notify_warning=lambda message: safe_notify(
                        f"Paths unavailable in Explore ({message})",
                        type="warning",
                    ),
                )

            @guard_ui_action(title="Load explore failed")
            async def _load() -> None:
                await load_explore_courses(
                    state=state,
                    courses_controller=courses_controller,
                    refresh_ui=list_view.refresh,
                    refresh_filter_options=_refresh_filter_options,
                    spawn_background_loads=lambda: (
                        asyncio.create_task(_load_articles_background()) if settings.feature_articles else None,
                        asyncio.create_task(_load_paths_background()),
                    ),
                )

            async def _set_tracking(course_id: int, status: str) -> None:
                await set_explore_tracking_status(
                    state=state,
                    courses_controller=courses_controller,
                    course_id=int(course_id),
                    status=str(status),
                    refresh_ui=list_view.refresh,
                )

            async def _clear_tracking(course_id: int) -> None:
                await clear_explore_tracking_status(
                    state=state,
                    courses_controller=courses_controller,
                    course_id=int(course_id),
                    refresh_ui=list_view.refresh,
                )

            async def _select_path(path_id: int) -> None:
                pid = int(path_id)
                optimistic_state = PathsPageState(
                    selected_by_id=dict(state.selected_by_path_id or {}),
                    selected_detail_by_path_id=dict(state.selected_detail_by_path_id or {}),
                    tracking_by_course_id=dict(state.tracking_by_course_id or {}),
                )
                _, selected_detail = await paths_controller.select_path(path_id=pid, state=optimistic_state)
                state.selected_by_path_id[pid] = {"path_id": pid}
                if isinstance(selected_detail, dict):
                    state.selected_detail_by_path_id[pid] = selected_detail
                state.tracking_by_course_id = dict(optimistic_state.tracking_by_course_id or {})
                list_view.refresh()

            async def _unselect_path(path_id: int) -> None:
                pid = int(path_id)
                await paths_controller.unselect_path(path_id=pid)
                state.selected_by_path_id.pop(pid, None)
                state.selected_detail_by_path_id.pop(pid, None)
                list_view.refresh()

            async def _toggle_path_selection(path_id: int) -> None:
                pid = int(path_id)
                if pid in state.selected_by_path_id:
                    await _unselect_path(pid)
                else:
                    await _select_path(pid)

            def _course_actions(course_row: dict[str, Any], course_id: int, course_url: str) -> Any:
                async def _open_course_details(cid: int, focus: bool) -> None:
                    suffix = "&view=reviews" if bool(focus) else ""
                    ui.navigate.to(f"/courses?course_id={int(cid)}{suffix}")

                async def _open_course_recommend(cid: int) -> None:
                    ui.navigate.to(f"/courses?course_id={int(cid)}")

                async def _open_course_delete(cid: int) -> None:
                    ui.navigate.to(f"/courses?course_id={int(cid)}")

                return build_course_card_actions(
                    course_id=course_id,
                    course_url=course_url,
                    course_row=course_row,
                    on_open_details=_open_course_details,
                    on_open_recommend=_open_course_recommend,
                    on_open_edit=lambda row: ui.navigate.to(f"/courses?course_id={int(row.get('id') or 0)}"),
                    on_confirm_delete=_open_course_delete,
                )

            async def _open_article_details(_: dict[str, Any], __: bool) -> None:
                ui.navigate.to("/articles")

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

                if tab_value == "courses":
                    shown_paths = []
                    shown_articles = []
                elif tab_value == "paths":
                    shown_courses = []
                    shown_articles = []
                elif tab_value == "articles":
                    shown_courses = []
                    shown_paths = []

                _refresh_meta(
                    course_count=len(shown_courses),
                    path_count=len(shown_paths),
                    article_count=len(shown_articles),
                    tab_value=tab_value,
                )

                if not shown_courses and not shown_paths and not shown_articles:
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        if not state.loaded_once:
                            ui.label("Discovery feed unavailable").classes("lp-courses-section-title")
                            ui.label("Explore could not load right now. Refresh to retry.").classes(
                                "lp-courses-section-subtitle"
                            )
                        else:
                            ui.label("No matches in Explore").classes("lp-courses-section-title")
                            ui.label("Adjust search scope or filters to discover more content.").classes(
                                "lp-courses-section-subtitle"
                            )
                    return

                def _render_course_item(course: dict[str, Any], *, item_classes: str) -> None:
                    with ui.element("div").classes(item_classes):
                        course_id = int(course.get("id") or 0)
                        tracked = state.tracking_by_course_id.get(course_id)
                        url = str(course.get("url") or "").strip()
                        can_edit = bool(is_admin or (str(course.get("created_by") or "") == username))
                        card_vm = map_course_card_view(
                            course_row=course,
                            tracked_row=tracked if isinstance(tracked, dict) else None,
                            review_summary_row=state.course_review_summary_by_course_id.get(course_id),
                            recommendation_summary_row=state.course_recommendation_summary_by_course_id.get(course_id),
                        )
                        render_course_card(
                            course_row=course,
                            tracked_row=tracked if isinstance(tracked, dict) else None,
                            card_vm=card_vm,
                            can_edit=can_edit,
                            has_url=bool(url),
                            actions=_course_actions(course, course_id, url),
                            is_tracked_course=lambda cid: int(cid) in state.tracking_by_course_id,
                            resolve_status_value=resolve_tracking_status_value,
                            on_set_status=_set_tracking,
                            on_clear_status=_clear_tracking,
                            has_video_preview=False,
                            is_preview_open=False,
                            preview_embed_url="",
                            on_toggle_preview=lambda: None,
                        )

                def _render_path_item(path: dict[str, Any]) -> None:
                    path_id = int(path.get("id") or 0)
                    is_tracked = path_id in state.selected_by_path_id
                    can_edit = bool(is_admin or (str(path.get("created_by") or "") == username))
                    card_vm = map_path_card_view(
                        path_row=path,
                        is_tracked=is_tracked,
                        detail=state.selected_detail_by_path_id.get(path_id),
                        tracking_by_course_id=dict(state.tracking_by_course_id or {}),
                        review_summary_row=state.path_review_summary_by_id.get(path_id),
                        recommendation_summary_row=state.path_recommendation_summary_by_id.get(path_id),
                    )
                    track_toggle_label = "Unselect" if is_tracked else "Select"

                    async def _on_track_toggle() -> None:
                        await _toggle_path_selection(path_id)

                    render_path_card(
                        path_row=path,
                        card_class_suffix=card_vm.card_class_suffix,
                        is_new=card_vm.is_new,
                        is_updated=card_vm.is_updated,
                        rating_badge=card_vm.rating_badge,
                        recommendation_badge=card_vm.recommendation_badge,
                        can_edit=can_edit,
                        shared_by=card_vm.shared_by,
                        tracking_label_text=card_vm.tracking_label_text,
                        tracking_chip_cls=card_vm.tracking_chip_cls,
                        completed=card_vm.completed,
                        total_courses=card_vm.total_courses,
                        progress=card_vm.progress,
                        milestone=card_vm.milestone,
                        milestone_class=card_vm.milestone_class,
                        impact=card_vm.impact,
                        next_title=card_vm.next_title,
                        on_review=lambda _pid=path_id: ui.navigate.to(f"/paths?path_id={int(_pid)}&view=reviews"),
                        on_recommend=lambda _pid=path_id: ui.navigate.to(f"/paths?path_id={int(_pid)}"),
                        on_copy_link=lambda _pid=path_id: copy_path_link(path_id=int(_pid)),
                        on_edit=lambda _pid=path_id: ui.navigate.to(f"/paths?path_id={int(_pid)}"),
                        on_delete=lambda _pid=path_id: ui.navigate.to(f"/paths?path_id={int(_pid)}"),
                        on_view=lambda _pid=path_id: ui.navigate.to(f"/paths?path_id={int(_pid)}"),
                        on_track_toggle=_on_track_toggle,
                        track_toggle_label=track_toggle_label,
                    )

                if shown_courses:
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        ui.label("Course picks").classes("lp-courses-section-title")
                    render_courses_catalog(
                        shown_page=shown_courses,
                        render_course_item=_render_course_item,
                        featured_title="Spotlight course",
                        featured_subtitle="Top match for your current query",
                        collection_title="More courses",
                    )

                if shown_paths:
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        ui.label("Path picks").classes("lp-courses-section-title")
                        ui.label("Top match for your current query").classes("lp-courses-section-subtitle")
                    featured_path = shown_paths[0]
                    remaining_paths = shown_paths[1:]
                    with ui.element("div").classes("lp-courses-grid"):
                        _render_path_item(featured_path)
                    if remaining_paths:
                        with ui.grid().classes("w-full gap-3 md:grid-cols-2"):
                            for row in remaining_paths:
                                _render_path_item(row)

                if shown_articles:
                    grouped_articles: list[dict[str, Any]] = []
                    for row in shown_articles:
                        tags = parse_tags(str(row.get("tags") or ""))
                        group_name = str(tags[0] if tags else "General")
                        grouped_articles.append({**row, "_explore_group": group_name})

                    def _render_article_item(article: dict[str, Any]) -> None:
                        article_id = int(article.get("id") or 0)
                        vm = map_article_card_view(
                            article_row=article,
                            review_summary_row=state.article_review_summary_by_article_id.get(article_id),
                        )
                        actions = build_article_card_actions(
                            article_row=article,
                            on_open_details=_open_article_details,
                        )
                        render_article_card(
                            article_row=article,
                            is_new=vm.is_new,
                            tags=vm.tags,
                            summary_text=vm.summary_text,
                            subtitle_text=vm.subtitle_text,
                            thumbnail_url=vm.thumbnail_url,
                            view_action=actions.on_view,
                            review_action=actions.on_review,
                        )

                    featured_article = grouped_articles[0]
                    remaining_articles = grouped_articles[1:]
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        ui.label("Article picks").classes("lp-courses-section-title")
                        ui.label("Top match for your current query").classes("lp-courses-section-subtitle")
                        _render_article_item(featured_article)

                    if remaining_articles:
                        render_explore_article_rails(
                            shown_articles=remaining_articles,
                            render_article_item=_render_article_item,
                        )

            def _on_search_change(*_args: Any) -> None:
                nonlocal search_telemetry_emitted
                if not search_telemetry_emitted and str(topbar.search_input.value or "").strip():
                    search_telemetry_emitted = True
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
