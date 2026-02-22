"""Explore page with unified discovery across courses and articles."""

from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
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
    set_explore_tracking_status,
)
from frontend.ui.nicegui.pages.explore.sections import (
    render_explore_article_rails,
    render_explore_filters_dialog,
    render_explore_topbar,
)
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.explore.ui_glue import compute_explore_meta_text, normalize_sort, normalize_tab


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/explore` route."""

    @ui.page("/explore")
    async def explore_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        courses_controller = CoursesPageController(api=api)
        articles_controller = ArticlesPageController(api=api)

        render_shell(title="Explore", store=store, api=api)

        request = getattr(ui.context.client, "request", None)
        query_params = getattr(request, "query_params", None)
        initial_tab = normalize_tab((query_params or {}).get("tab", "all") if query_params is not None else "all")

        state = ExplorePageState()

        with render_catalog_scope(variant="explore").classes("lp-container"):

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

            topbar = render_explore_topbar(initial_tab=initial_tab, on_open_filters=lambda: filter_controls.dialog.open())
            filter_controls = render_explore_filters_dialog(on_reset=_reset_filters)

            def _refresh_meta(*, course_count: int, article_count: int, tab_value: str) -> None:
                topbar.meta.text = compute_explore_meta_text(
                    tab_value=tab_value,
                    course_count=course_count,
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

            @guard_ui_action(title="Load explore failed")
            async def _load() -> None:
                await load_explore_courses(
                    state=state,
                    courses_controller=courses_controller,
                    refresh_ui=list_view.refresh,
                    refresh_filter_options=_refresh_filter_options,
                    spawn_articles_load=(
                        lambda: asyncio.create_task(_load_articles_background()) if settings.feature_articles else None
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

                if tab_value == "courses":
                    shown_articles = []
                elif tab_value == "articles":
                    shown_courses = []

                _refresh_meta(course_count=len(shown_courses), article_count=len(shown_articles), tab_value=tab_value)

                if not shown_courses and not shown_articles:
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        if not state.loaded_once:
                            ui.label("Discovery feed unavailable").classes("lp-courses-section-title")
                            ui.label("Explore could not load right now. Refresh to retry.").classes("lp-courses-section-subtitle")
                        else:
                            ui.label("No matches in Explore").classes("lp-courses-section-title")
                            ui.label("Adjust search scope or filters to discover more content.").classes("lp-courses-section-subtitle")
                    return

                def _render_course_item(course: dict[str, Any], *, item_classes: str) -> None:
                    with ui.element("div").classes(item_classes):
                        course_id = int(course.get("id") or 0)
                        tracked = state.tracking_by_course_id.get(course_id)
                        url = str(course.get("url") or "").strip()
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
                            can_edit=False,
                            has_url=bool(url),
                            actions=_course_actions(course, course_id, url),
                            is_tracked_course=lambda cid: int(cid) in state.tracking_by_course_id,
                            resolve_status_value=resolve_tracking_status_value,
                            on_set_status=_set_tracking,
                            on_clear_status=_clear_tracking,
                            has_video_preview=bool(card_vm.has_video_preview),
                            is_preview_open=bool(int(state.preview_course_id or 0) == int(course_id)),
                            preview_embed_url=str(card_vm.video_embed_url or ""),
                            on_toggle_preview=lambda _cid=course_id: (
                                setattr(
                                    state,
                                    "preview_course_id",
                                    None if int(state.preview_course_id or 0) == int(_cid) else int(_cid),
                                ),
                                list_view.refresh(),
                            ),
                        )

                if shown_courses:
                    with ui.column().classes("w-full gap-2 lp-courses-section"):
                        ui.label("Course picks").classes("lp-courses-section-title")
                    render_courses_catalog(
                        shown_page=shown_courses,
                        render_course_item=_render_course_item,
                        featured_title="Spotlight course",
                        featured_subtitle="Popular for your current query",
                        collection_title="Explore by category",
                    )

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

                    render_explore_article_rails(
                        shown_articles=grouped_articles,
                        render_article_item=_render_article_item,
                    )

            topbar.search_input.on("update:model-value", lambda *_: list_view.refresh())
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
