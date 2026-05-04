"""Explore-local gateway that isolates cross-page controller wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.domains.articles.controller import ArticlesPageController
from frontend.ui.nicegui.domains.courses.controller import CourseDetailBundle, CoursesPageController
from frontend.ui.nicegui.domains.paths.controller import PathsPageController
from frontend.ui.nicegui.domains.paths.state import PathsPageState
from frontend.ui.nicegui.domains.videos.controller import VideosPageController


@dataclass(slots=True)
class ExploreCoursesAccess:
    """Course-domain operations used by Explore orchestration."""

    _controller: CoursesPageController

    async def load_list_bundle(self, *, params: dict[str, Any] | None) -> Any:
        """Load courses list bundle for Explore.

        Args:
            params: Optional query params for the courses list.

        Returns:
            Courses list payload bundle.

        """
        return await self._controller.load_list_bundle(params=params)

    async def create_course(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new course from Explore share flow.

        Args:
            payload: Course create payload.

        Returns:
            Created course payload.

        """
        return await self._controller.create_course(payload=dict(payload or {}))

    async def suggest_course_from_url(self, *, url: str) -> dict[str, Any]:
        """Suggest course metadata from a URL.

        Args:
            url: Source URL.

        Returns:
            Suggestion payload.

        """
        return await self._controller.suggest_course_from_url(url=str(url or ""))

    async def set_tracking_status(self, *, course_id: int, status: str) -> None:
        """Set course tracking status.

        Args:
            course_id: Course identifier.
            status: New tracking status value.

        """
        await self._controller.set_tracking_status(course_id=int(course_id), status=str(status))

    async def clear_tracking_status(self, *, course_id: int) -> None:
        """Clear course tracking status.

        Args:
            course_id: Course identifier.

        """
        await self._controller.clear_tracking_status(course_id=int(course_id))

    async def load_course_detail_bundle(self, *, course_id: int, cache_scope: str) -> CourseDetailBundle:
        """Load course detail bundle for Explore detail surfaces.

        Args:
            course_id: Course identifier.
            cache_scope: Cache scope key.

        Returns:
            Detail payload bundle.

        """
        return await self._controller.load_course_detail_bundle(course_id=int(course_id), cache_scope=str(cache_scope or ""))

    async def save_course_review(self, *, course_id: int, rating: int, text: str, cache_scope: str) -> dict[str, Any]:
        """Create or update course review via courses controller.

        Args:
            course_id: Course identifier.
            rating: Review rating.
            text: Review comment text.
            cache_scope: Cache scope key.

        Returns:
            Saved review payload.

        """
        return await self._controller.save_course_review(
            course_id=int(course_id),
            rating=int(rating),
            text=str(text or ""),
            cache_scope=str(cache_scope or ""),
        )

    async def delete_course_review(self, *, course_id: int, review_id: int, cache_scope: str) -> bool:
        """Delete a course review via courses controller.

        Args:
            course_id: Course identifier.
            review_id: Review identifier.
            cache_scope: Cache scope key.

        Returns:
            `True` when deletion succeeds.

        """
        return await self._controller.delete_course_review(
            course_id=int(course_id),
            review_id=int(review_id),
            cache_scope=str(cache_scope or ""),
        )


@dataclass(slots=True)
class ExplorePathsAccess:
    """Path-domain operations used by Explore orchestration."""

    _controller: PathsPageController

    async def load_all(self, *, state: PathsPageState) -> None:
        """Load all paths data into shared state.

        Args:
            state: Path state container used by Explore.

        """
        await self._controller.load_all(state=state)

    async def select_path(self, *, path_id: int, state: PathsPageState) -> tuple[int, dict[str, Any] | None]:
        """Select a path and seed tracking where needed.

        Args:
            path_id: Path identifier.
            state: Path state container used by Explore.

        Returns:
            Seeded tracking count and optional selected path detail row.

        """
        return await self._controller.select_path(path_id=int(path_id), state=state)

    async def unselect_path(self, *, path_id: int) -> bool:
        """Unselect a path.

        Args:
            path_id: Path identifier.

        Returns:
            `True` when unselect succeeds.

        """
        return await self._controller.unselect_path(path_id=int(path_id))

    async def create_path(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new path from Explore share flow.

        Args:
            payload: Path create payload.

        Returns:
            Created path payload.

        """
        return await self._controller.create_path(payload=dict(payload or {}))


@dataclass(slots=True)
class ExploreArticlesAccess:
    """Article-domain operations used by Explore orchestration."""

    _controller: ArticlesPageController

    async def load_list_bundle(self) -> Any:
        """Load Explore article list bundle.

        Returns:
            Articles list payload bundle.

        """
        return await self._controller.load_list_bundle()

    async def create_article(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new article from Explore share flow.

        Args:
            payload: Article create payload.

        Returns:
            Created article payload.

        """
        return await self._controller.create_article(payload=dict(payload or {}))

    async def suggest_article_from_url(self, *, url: str) -> dict[str, Any]:
        """Suggest article metadata from a URL.

        Args:
            url: Source URL.

        Returns:
            Suggestion payload.

        """
        return await self._controller.suggest_article_from_url(url=str(url or ""))


@dataclass(slots=True)
class ExploreVideosAccess:
    """Video-domain operations used by Explore orchestration."""

    _controller: VideosPageController

    async def load_list(self) -> list[dict[str, Any]]:
        """Load Explore videos list."""
        return await self._controller.load_list()

    async def create_video(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new video from share flow."""
        return await self._controller.create_video(payload=dict(payload or {}))

    async def suggest_video_from_url(self, *, url: str) -> dict[str, Any]:
        """Suggest video metadata from a URL."""
        return await self._controller.suggest_video_from_url(url=str(url or ""))

    async def load_video(self, *, video_id: int) -> dict[str, Any]:
        """Load one video detail payload."""
        return await self._controller.load_video(video_id=int(video_id))


@dataclass(slots=True)
class ExploreDataGateway:
    """Facade owning cross-page controllers used by Explore."""

    courses: ExploreCoursesAccess
    paths: ExplorePathsAccess
    articles: ExploreArticlesAccess
    videos: ExploreVideosAccess

    @classmethod
    def from_api(cls, *, api: ApiClient) -> ExploreDataGateway:
        """Build gateway and underlying controllers from a shared API client.

        Args:
            api: Shared API client.

        Returns:
            Configured Explore gateway.

        """
        return cls(
            courses=ExploreCoursesAccess(_controller=CoursesPageController(api=api)),
            paths=ExplorePathsAccess(_controller=PathsPageController(api=api)),
            articles=ExploreArticlesAccess(_controller=ArticlesPageController(api=api)),
            videos=ExploreVideosAccess(_controller=VideosPageController(api=api)),
        )
