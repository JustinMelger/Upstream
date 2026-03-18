"""Controller/orchestration for dedicated learning-item share pages."""

from __future__ import annotations

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.item_helpers import encode_path_item_ref, learning_item_option_label
from frontend.ui.nicegui.pages.videos.controller import VideosPageController


class SharePageController:
    """Imperative API workflows for `/share/item` and compatibility redirects."""

    def __init__(self, *, api: ApiClient):
        """Initialize the share-page controller."""
        self._courses = CoursesPageController(api=api)
        self._articles = ArticlesPageController(api=api)
        self._paths = PathsPageController(api=api)
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

    async def load_path_learning_item_options(self) -> dict[str, str]:
        """Load selectable learning-item options for path sharing."""
        bundle = await self._courses.load_list_bundle()
        video_rows = await self._videos.load_list()
        article_bundle = await self._articles.load_list_bundle()
        options: dict[str, str] = {}
        for row in list(bundle.courses or []):
            course_id = int(row.get("id") or 0)
            if course_id <= 0:
                continue
            options[encode_path_item_ref(item_type="course", item_id=course_id)] = learning_item_option_label(
                item_type="course", row=row
            )
        for row in list(video_rows or []):
            video_id = int(row.get("id") or 0)
            if video_id <= 0:
                continue
            options[encode_path_item_ref(item_type="video", item_id=video_id)] = learning_item_option_label(
                item_type="video", row=row
            )
        for row in list(article_bundle.articles or []):
            article_id = int(row.get("id") or 0)
            if article_id <= 0:
                continue
            options[encode_path_item_ref(item_type="article", item_id=article_id)] = learning_item_option_label(
                item_type="article", row=row
            )
        return options

    async def create_path(self, *, payload: dict[str, object]) -> dict[str, object]:
        """Create a path row from the dedicated share-path page."""
        return dict(await self._paths.create_path(payload=dict(payload or {})) or {})
