"""UI action builders for Explore page cards."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.courses.actions import build_course_card_actions
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.state import ExplorePageState


def build_explore_course_actions(
    *,
    course_row: dict[str, Any],
    course_id: int,
    course_url: str,
    username: str,
    is_admin: bool,
    state: ExplorePageState,
    controller: ExplorePageController,
    on_set_tracking: Any,
    on_clear_tracking: Any,
) -> Any:
    """Build course card actions for Explore."""

    async def _open_explore_course_details(cid: int, focus: bool) -> None:
        course_id_int = int(cid)
        mode_qs = "?view=reviews" if bool(focus) else ""
        ui.navigate.to(f"/explore/courses/{course_id_int}{mode_qs}")

    async def _open_course_details(cid: int, focus: bool) -> None:
        _ = course_row
        await _open_explore_course_details(int(cid), bool(focus))

    async def _open_course_delete(cid: int) -> None:
        ui.navigate.to(f"/explore/courses/{int(cid)}")

    return build_course_card_actions(
        course_id=course_id,
        course_url=course_url,
        course_row=course_row,
        on_open_details=_open_course_details,
        on_open_edit=lambda row: ui.navigate.to(f"/explore/courses/{int(row.get('id') or 0)}"),
        on_confirm_delete=_open_course_delete,
    )


async def open_explore_article_details(article_row: dict[str, Any], focus_reviews: bool) -> None:
    """Open dedicated article detail page from Explore article cards."""
    article_id = int(article_row.get("id") or 0)
    mode_qs = "?view=reviews" if bool(focus_reviews) else ""
    ui.navigate.to(f"/explore/articles/{article_id}{mode_qs}")
