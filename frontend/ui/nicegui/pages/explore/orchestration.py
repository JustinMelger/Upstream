"""State orchestration helpers for the Explore page."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.paths.state import PathsPageState


async def load_explore_courses(
    *,
    state: ExplorePageState,
    courses_controller: Any,
    refresh_ui: Callable[..., Any],
    refresh_filter_options: Callable[..., Any],
    spawn_background_loads: Callable[[], None],
) -> None:
    """Load courses and related summaries for Explore."""
    state.loading = True
    refresh_ui()
    try:
        bundle = await courses_controller.load_list_bundle(params=None)
        state.courses = list(bundle.courses or [])
        state.tracking_by_course_id = dict(bundle.tracking_by_course_id or {})
        state.course_review_summary_by_course_id = dict(bundle.review_summary_by_course_id or {})
        state.loaded_once = True
        refresh_filter_options()
        refresh_ui()
        spawn_background_loads()
    finally:
        state.loading = False
        refresh_ui()


async def load_explore_paths_background(
    *,
    state: ExplorePageState,
    paths_controller: Any,
    refresh_ui: Callable[..., Any],
    notify_warning: Callable[[str], None],
) -> None:
    """Best-effort path load that should not block course rendering."""
    if state.paths_loading:
        return

    state.paths_loading = True
    refresh_ui()
    try:
        paths_state = PathsPageState()
        await asyncio.wait_for(paths_controller.load_all(state=paths_state), timeout=8.0)
        state.paths = list(paths_state.paths or [])
        state.selected_by_path_id = dict(paths_state.selected_by_id or {})
        state.selected_detail_by_path_id = dict(paths_state.selected_detail_by_path_id or {})
        state.path_review_summary_by_id = dict(paths_state.path_review_summary_by_id or {})
        if paths_state.tracking_by_course_id:
            state.tracking_by_course_id = dict(paths_state.tracking_by_course_id)
    except (ApiError, TimeoutError) as exc:
        state.paths = []
        state.selected_by_path_id = {}
        state.selected_detail_by_path_id = {}
        state.path_review_summary_by_id = {}
        notify_warning(str(exc))
    finally:
        state.paths_loading = False
        refresh_ui()


async def load_explore_articles_background(
    *,
    state: ExplorePageState,
    feature_articles_enabled: bool,
    articles_controller: Any,
    refresh_ui: Callable[..., Any],
    refresh_filter_options: Callable[..., Any],
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


async def load_explore_videos_background(
    *,
    state: ExplorePageState,
    videos_controller: Any,
    refresh_ui: Callable[..., Any],
    notify_warning: Callable[[str], None],
) -> None:
    """Best-effort video load that should not block course rendering."""
    if state.videos_loading:
        return

    state.videos_loading = True
    refresh_ui()
    try:
        videos_bundle = await asyncio.wait_for(videos_controller.load_list_bundle(params=None), timeout=6.0)
        state.videos = list(videos_bundle.videos or [])
        state.video_review_summary_by_video_id = dict(videos_bundle.review_summary_by_video_id or {})
    except (ApiError, TimeoutError) as exc:
        state.videos = []
        state.video_review_summary_by_video_id = {}
        notify_warning(str(exc))
    finally:
        state.videos_loading = False
        refresh_ui()


async def set_explore_tracking_status(
    *,
    state: ExplorePageState,
    courses_controller: Any,
    course_id: int,
    status: str,
    refresh_ui: Callable[..., Any],
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
    refresh_ui: Callable[..., Any],
) -> None:
    """Clear course tracking status and update local state."""
    cid = int(course_id)
    await courses_controller.clear_tracking_status(course_id=cid)
    state.tracking_by_course_id.pop(cid, None)
    refresh_ui()
