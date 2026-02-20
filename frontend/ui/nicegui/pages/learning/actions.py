"""UI-facing navigation actions for the Learning page."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.core.navigation_intents import set_course_intent, set_path_intent


@dataclass(slots=True)
class LearningNavigationActions:
    """Navigation action factory for course/path deep links."""

    username: str
    build_course_navigation_url: Callable[[int, str], str]
    build_path_navigation_url: Callable[[int, str], str]

    def make_course_view_action(self, course_id: int) -> Any:
        async def _view_course() -> None:
            set_course_intent(username=self.username, course_id=int(course_id), view="full")
            app.storage.user["courses_open_intent"] = {
                "course_id": int(course_id),
                "view": "full",
            }
            url = self.build_course_navigation_url(int(course_id), "full")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _view_course

    def make_course_review_action(self, course_id: int) -> Any:
        async def _review_course() -> None:
            set_course_intent(username=self.username, course_id=int(course_id), view="reviews")
            app.storage.user["courses_open_intent"] = {
                "course_id": int(course_id),
                "view": "reviews",
            }
            url = self.build_course_navigation_url(int(course_id), "reviews")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _review_course

    def make_path_view_action(self, path_id: int) -> Any:
        async def _view_path() -> None:
            set_path_intent(username=self.username, path_id=int(path_id), view="full")
            app.storage.user["paths_open_intent"] = {
                "path_id": int(path_id),
                "view": "full",
            }
            url = self.build_path_navigation_url(int(path_id), "full")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _view_path

    def make_path_review_action(self, path_id: int) -> Any:
        async def _review_path() -> None:
            set_path_intent(username=self.username, path_id=int(path_id), view="reviews")
            app.storage.user["paths_open_intent"] = {
                "path_id": int(path_id),
                "view": "reviews",
            }
            url = self.build_path_navigation_url(int(path_id), "reviews")
            ui.run_javascript(f"window.location.href={json.dumps(url)};")

        return _review_path

    def navigate_tab(self, tab: str) -> None:
        ui.navigate.to(f"/learning?tab={str(tab or 'learning')}")
