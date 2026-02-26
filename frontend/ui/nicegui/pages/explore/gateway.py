"""Explore-local gateway that isolates cross-page controller wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.courses.controller import CourseDetailBundle, CoursesPageController
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.state import PathsPageState


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


@dataclass(slots=True)
class ExploreDataGateway:
    """Facade owning cross-page controllers used by Explore."""

    courses: ExploreCoursesAccess
    paths: ExplorePathsAccess
    articles: ExploreArticlesAccess

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
        )
