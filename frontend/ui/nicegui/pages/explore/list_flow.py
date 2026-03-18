"""Flow helpers for building Explore list section dependencies."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.explore.actions import build_explore_course_actions, open_explore_article_details
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.list_sections import ExploreSectionsDeps
from frontend.ui.nicegui.pages.explore.state import ExplorePageState


@dataclass(frozen=True, slots=True)
class ExploreSectionsUiControls:
    """UI-only controls/state consumed by Explore section rendering."""

    learning_items_visible_limit: int
    on_show_more_learning_items: Callable[[], None]


def build_sections_deps(
    *,
    state: ExplorePageState,
    username: str,
    is_admin: bool,
    show_all_categories: bool,
    controller: ExplorePageController,
    on_set_tracking: Callable[[int, str], Awaitable[None]],
    on_clear_tracking: Callable[[int], Awaitable[None]],
    on_toggle_path_selection: Callable[[int], Awaitable[None]],
    on_open_path: Callable[[int], None],
    ui_controls: ExploreSectionsUiControls,
) -> ExploreSectionsDeps:
    """Build the dependency bundle consumed by `render_explore_sections`."""
    return ExploreSectionsDeps(
        state=state,
        username=username,
        is_admin=is_admin,
        show_all_categories=bool(show_all_categories),
        course_actions_builder=lambda course_row, course_id, course_url: build_explore_course_actions(
            course_row=course_row,
            course_id=course_id,
            course_url=course_url,
            username=username,
            is_admin=is_admin,
            state=state,
            controller=controller,
            on_set_tracking=on_set_tracking,
            on_clear_tracking=on_clear_tracking,
        ),
        on_set_tracking=on_set_tracking,
        on_clear_tracking=on_clear_tracking,
        on_toggle_path_selection=on_toggle_path_selection,
        open_path=on_open_path,
        open_article_details=open_explore_article_details,
        learning_items_visible_limit=int(ui_controls.learning_items_visible_limit or 8),
        on_show_more_learning_items=ui_controls.on_show_more_learning_items,
    )
