"""Controller/orchestration layer for the Explore page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.pages.explore.gateway import CourseDetailBundle, ExploreDataGateway
from frontend.ui.nicegui.pages.explore.orchestration import (
    clear_explore_tracking_status,
    load_explore_articles_background,
    load_explore_courses,
    load_explore_paths_background,
    set_explore_tracking_status,
)
from frontend.ui.nicegui.pages.explore.share_models import ExploreSharePayload, ExploreUrlValue
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.paths.state import PathsPageState


class ExplorePageController:
    """Imperative API workflow orchestration for Explore page."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller and domain gateway.

        Args:
            api: Shared API client.

        """
        self._gateway = ExploreDataGateway.from_api(api=api)

    async def load(
        self,
        *,
        state: ExplorePageState,
        refresh_ui: Callable[..., Any],
        refresh_filter_options: Callable[..., Any],
        notify_articles_warning: Callable[[str], None],
        notify_paths_warning: Callable[[str], None],
    ) -> None:
        """Load explore data with background path/article fetches."""

        async def _load_articles_background() -> None:
            await load_explore_articles_background(
                state=state,
                feature_articles_enabled=settings.feature_articles,
                articles_controller=self._gateway.articles,
                refresh_ui=refresh_ui,
                refresh_filter_options=refresh_filter_options,
                notify_warning=notify_articles_warning,
            )

        async def _load_paths_background() -> None:
            await load_explore_paths_background(
                state=state,
                paths_controller=self._gateway.paths,
                refresh_ui=refresh_ui,
                notify_warning=notify_paths_warning,
            )

        def _spawn_background_loads() -> None:
            if settings.feature_articles:
                asyncio.create_task(_load_articles_background())
            asyncio.create_task(_load_paths_background())

        await load_explore_courses(
            state=state,
            courses_controller=self._gateway.courses,
            refresh_ui=refresh_ui,
            refresh_filter_options=refresh_filter_options,
            spawn_background_loads=_spawn_background_loads,
        )

    async def set_tracking_status(
        self,
        *,
        state: ExplorePageState,
        course_id: int,
        status: str,
        refresh_ui: Callable[..., Any],
    ) -> None:
        """Persist tracking status for a course and update local page state."""
        await set_explore_tracking_status(
            state=state,
            courses_controller=self._gateway.courses,
            course_id=int(course_id),
            status=str(status),
            refresh_ui=refresh_ui,
        )

    async def clear_tracking_status(
        self,
        *,
        state: ExplorePageState,
        course_id: int,
        refresh_ui: Callable[..., Any],
    ) -> None:
        """Clear tracking status for a course and update local page state."""
        await clear_explore_tracking_status(
            state=state,
            courses_controller=self._gateway.courses,
            course_id=int(course_id),
            refresh_ui=refresh_ui,
        )

    async def toggle_path_selection(
        self,
        *,
        state: ExplorePageState,
        path_id: int,
        refresh_ui: Callable[..., Any],
    ) -> None:
        """Toggle path selection state in Explore."""
        pid = int(path_id)
        if pid in state.selected_by_path_id:
            await self._gateway.paths.unselect_path(path_id=pid)
            state.selected_by_path_id.pop(pid, None)
            state.selected_detail_by_path_id.pop(pid, None)
            refresh_ui()
            return

        optimistic_state = PathsPageState(
            selected_by_id=dict(state.selected_by_path_id or {}),
            selected_detail_by_path_id=dict(state.selected_detail_by_path_id or {}),
            tracking_by_course_id=dict(state.tracking_by_course_id or {}),
        )
        _, selected_detail = await self._gateway.paths.select_path(path_id=pid, state=optimistic_state)
        state.selected_by_path_id[pid] = {"path_id": pid}
        if isinstance(selected_detail, dict):
            state.selected_detail_by_path_id[pid] = selected_detail
        state.tracking_by_course_id = dict(optimistic_state.tracking_by_course_id or {})
        refresh_ui()

    async def load_course_detail_bundle(self, *, course_id: int, cache_scope: str) -> CourseDetailBundle:
        """Load course detail payload for the Explore details dialog."""
        return await self._gateway.courses.load_course_detail_bundle(
            course_id=int(course_id), cache_scope=str(cache_scope or "")
        )

    async def save_course_review(
        self,
        *,
        course_id: int,
        rating: int,
        text: str,
        cache_scope: str,
    ) -> dict[str, Any]:
        """Save course review from Explore details dialog."""
        return await self._gateway.courses.save_course_review(
            course_id=int(course_id),
            rating=int(rating),
            text=str(text or ""),
            cache_scope=str(cache_scope or ""),
        )

    async def delete_course_review(
        self,
        *,
        course_id: int,
        review_id: int,
        cache_scope: str,
    ) -> bool:
        """Delete course review from Explore details dialog."""
        return await self._gateway.courses.delete_course_review(
            course_id=int(course_id),
            review_id=int(review_id),
            cache_scope=str(cache_scope or ""),
        )

    async def create_course_share(
        self,
        *,
        state: ExplorePageState,
        payload: ExploreSharePayload,
        reload_data: Callable[[], Awaitable[None]],
        refresh_ui: Callable[..., Any],
    ) -> dict[str, Any]:
        """Create a course from Explore share dialog and refresh the list view."""
        created = await self._gateway.courses.create_course(payload=dict(payload.payload or {}))
        await reload_data()
        refresh_ui()
        return created

    async def create_path_share(
        self,
        *,
        state: ExplorePageState,
        payload: ExploreSharePayload,
        reload_data: Callable[[], Awaitable[None]],
        refresh_ui: Callable[..., Any],
    ) -> None:
        """Create a path from Explore share dialog and refresh the list view."""
        _ = state
        await self._gateway.paths.create_path(payload=dict(payload.payload or {}))
        await reload_data()
        refresh_ui()

    async def create_article_share(
        self,
        *,
        state: ExplorePageState,
        payload: ExploreSharePayload,
        reload_data: Callable[[], Awaitable[None]],
        refresh_ui: Callable[..., Any],
    ) -> dict[str, Any]:
        """Create an article from Explore share dialog and refresh the list view."""
        _ = state
        created = await self._gateway.articles.create_article(payload=dict(payload.payload or {}))
        await reload_data()
        refresh_ui()
        return created

    async def suggest_course_from_url(self, *, url_value: ExploreUrlValue) -> dict[str, Any]:
        """Suggest course metadata from URL for Explore share dialog."""
        return await self._gateway.courses.suggest_course_from_url(url=str(url_value.url or ""))

    async def suggest_article_from_url(self, *, url_value: ExploreUrlValue) -> dict[str, Any]:
        """Suggest article metadata from URL for Explore share dialog."""
        return await self._gateway.articles.suggest_article_from_url(url=str(url_value.url or ""))

    def is_duplicate_course_url(self, *, state: ExplorePageState, url_value: ExploreUrlValue) -> bool:
        """Check whether a course URL already exists in loaded Explore results."""
        normalized = str(url_value.url or "").strip().lower()
        if not normalized:
            return False
        for row in list(state.courses or []):
            if str(row.get("url") or "").strip().lower() == normalized:
                return True
        return False

    def is_duplicate_article_url(self, *, state: ExplorePageState, url_value: ExploreUrlValue) -> bool:
        """Check whether an article URL already exists in loaded Explore results."""
        normalized = str(url_value.url or "").strip().lower()
        if not normalized:
            return False
        for row in list(state.articles or []):
            if str(row.get("url") or "").strip().lower() == normalized:
                return True
        return False

    def build_path_share_course_options(self, *, state: ExplorePageState) -> dict[int, str]:
        """Build course options map used by Explore path-share dialog."""
        options: dict[int, str] = {}
        for row in list(state.courses or []):
            try:
                cid = int(row.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid <= 0:
                continue
            options[cid] = f"{str(row.get('title') or '').strip()} (#{cid})"
        return options
