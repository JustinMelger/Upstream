"""UI-facing navigation actions for the Learning page."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.navigation import build_learning_tab_link
from frontend.ui.nicegui.pages.learning.state import LearningPageState


@dataclass(slots=True)
class LearningNavigationActions:
    """Navigation action factory for course/path deep links."""

    username: str
    build_course_navigation_url: Callable[[int, str], str]
    build_path_navigation_url: Callable[[int, str], str]

    def make_course_view_action(self, course_id: int) -> Any:
        """Build a callback that opens course details.

        Args:
            course_id: Course identifier to open.

        Returns:
            Async callback for UI action binding.

        """

        async def _view_course() -> None:
            url = self.build_course_navigation_url(int(course_id), "full")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _view_course

    def make_course_review_action(self, course_id: int) -> Any:
        """Build a callback that opens course reviews mode.

        Args:
            course_id: Course identifier to open.

        Returns:
            Async callback for UI action binding.

        """

        async def _review_course() -> None:
            url = self.build_course_navigation_url(int(course_id), "reviews")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _review_course

    def make_path_view_action(self, path_id: int) -> Any:
        """Build a callback that opens path details.

        Args:
            path_id: Path identifier to open.

        Returns:
            Async callback for UI action binding.

        """

        async def _view_path() -> None:
            url = self.build_path_navigation_url(int(path_id), "full")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _view_path

    def make_path_review_action(self, path_id: int) -> Any:
        """Build a callback that opens path reviews mode.

        Args:
            path_id: Path identifier to open.

        Returns:
            Async callback for UI action binding.

        """

        async def _review_path() -> None:
            url = self.build_path_navigation_url(int(path_id), "reviews")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _review_path

    def make_article_view_action(self, article_id: int) -> Any:
        """Build a callback that opens article details."""

        async def _view_article() -> None:
            ui.navigate.to(f"/explore/articles/{int(article_id)}")

        return _view_article

    def make_video_view_action(self, video_id: int) -> Any:
        """Build a callback that opens video details."""

        async def _view_video() -> None:
            ui.navigate.to(f"/explore/videos/{int(video_id)}")

        return _view_video

    def make_video_review_action(self, video_id: int) -> Any:
        """Build a callback that opens video details for review flow."""

        async def _review_video() -> None:
            ui.navigate.to(f"/explore/videos/{int(video_id)}")

        return _review_video

    def navigate_tab(self, tab: str) -> None:
        """Navigate to a specific learning tab.

        Args:
            tab: Target tab key.

        """
        ui.navigate.to(build_learning_tab_link(tab=str(tab)))


def load_more_tracked(*, state: LearningPageState, total_count: int, refresh: Callable[[], None]) -> None:
    """Increase tracked section visible count and refresh content."""
    state.tracked_visible = min(int(total_count), int(state.tracked_visible) + int(state.page_size))
    refresh()


def load_more_selected(*, state: LearningPageState, total_count: int, refresh: Callable[[], None]) -> None:
    """Increase selected section visible count and refresh content."""
    state.selected_visible = min(int(total_count), int(state.selected_visible) + int(state.page_size))
    refresh()
