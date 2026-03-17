"""Controller/orchestration for dedicated learning-item share pages."""

from __future__ import annotations

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.videos.controller import VideosPageController


class SharePageController:
    """Imperative API workflows for `/share/item` and compatibility redirects."""

    def __init__(self, *, api: ApiClient):
        """Initialize the share-page controller."""
        self._courses = CoursesPageController(api=api)
        self._articles = ArticlesPageController(api=api)
        self._videos = VideosPageController(api=api)

    async def suggest_course_from_url(self, *, url: str) -> dict[str, object]:
        """Suggest course metadata from URL."""
        return dict(await self._courses.suggest_course_from_url(url=str(url or "")) or {})

    async def create_course(self, *, payload: dict[str, object]) -> dict[str, object]:
        """Create a course row from share form payload."""
        return dict(await self._courses.create_course(payload=dict(payload or {})) or {})

    async def suggest_video_from_url(self, *, url: str) -> dict[str, object]:
        """Suggest video metadata from URL."""
        return dict(await self._videos.suggest_video_from_url(url=str(url or "")) or {})

    async def create_video(self, *, payload: dict[str, object]) -> dict[str, object]:
        """Create a video row from share form payload."""
        return dict(await self._videos.create_video(payload=dict(payload or {})) or {})

    async def suggest_article_from_url(self, *, url: str) -> dict[str, object]:
        """Suggest article metadata from URL."""
        return dict(await self._articles.suggest_article_from_url(url=str(url or "")) or {})

    async def create_article(self, *, payload: dict[str, object]) -> dict[str, object]:
        """Create an article row from share form payload."""
        return dict(await self._articles.create_article(payload=dict(payload or {})) or {})
