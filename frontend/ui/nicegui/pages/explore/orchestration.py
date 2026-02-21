"""State orchestration helpers for the Explore page."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.explore.state import ExplorePageState


async def load_explore_courses(
    *,
    state: ExplorePageState,
    courses_controller: Any,
    refresh_ui: Callable[[], None],
    refresh_filter_options: Callable[[], None],
    spawn_articles_load: Callable[[], None],
) -> None:
    """Load courses and related summaries for Explore."""
    state.loading = True
    refresh_ui()
    try:
        bundle = await courses_controller.load_list_bundle(params=None)
        state.courses = list(bundle.courses or [])
        state.tracking_by_course_id = dict(bundle.tracking_by_course_id or {})
        state.course_review_summary_by_course_id = dict(bundle.review_summary_by_course_id or {})
        state.course_recommendation_summary_by_course_id = dict(bundle.recommendation_summary_by_course_id or {})
        state.loaded_once = True
        refresh_filter_options()
        refresh_ui()
        spawn_articles_load()
    finally:
        state.loading = False
        refresh_ui()


async def load_explore_articles_background(
    *,
    state: ExplorePageState,
    feature_articles_enabled: bool,
    articles_controller: Any,
    refresh_ui: Callable[[], None],
    refresh_filter_options: Callable[[], None],
    notify_warning: Callable[[str], None],
) -> None:
    """Best-effort article load that should not block course rendering."""
    if not feature_articles_enabled:
        state.articles = []
        state.article_review_summary_by_article_id = {}
        return
    if state.articles_loading:
        return

    state.articles_loading = True
    refresh_ui()
    try:
        articles_bundle = await asyncio.wait_for(articles_controller.load_list_bundle(), timeout=6.0)
        state.articles = list(articles_bundle.articles or [])
        state.article_review_summary_by_article_id = dict(articles_bundle.review_summary_by_article_id or {})
    except (ApiError, TimeoutError) as exc:
        state.articles = []
        state.article_review_summary_by_article_id = {}
        notify_warning(str(exc))
    finally:
        state.articles_loading = False
        refresh_filter_options()
        refresh_ui()


async def set_explore_tracking_status(
    *,
    state: ExplorePageState,
    courses_controller: Any,
    course_id: int,
    status: str,
    refresh_ui: Callable[[], None],
) -> None:
    """Set course tracking status and update local state."""
    cid = int(course_id)
    value = str(status)
    await courses_controller.set_tracking_status(course_id=cid, status=value)
    state.tracking_by_course_id[cid] = {"course_id": cid, "status": value}
    refresh_ui()


async def clear_explore_tracking_status(
    *,
    state: ExplorePageState,
    courses_controller: Any,
    course_id: int,
    refresh_ui: Callable[[], None],
) -> None:
    """Clear course tracking status and update local state."""
    cid = int(course_id)
    await courses_controller.clear_tracking_status(course_id=cid)
    state.tracking_by_course_id.pop(cid, None)
    refresh_ui()
