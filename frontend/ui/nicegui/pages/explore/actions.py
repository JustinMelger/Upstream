"""UI action builders for Explore page cards."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.courses.actions import build_course_card_actions
from frontend.ui.nicegui.pages.courses.ui_glue import format_short_date, normalize_course_view_mode
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.detail_flow import (
    open_explore_article_details_dialog,
    open_explore_course_details_dialog,
)
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
        _ = str(course_url or "")
        course_id_int = int(cid)

        async def _on_set_tracking_status(status: str) -> None:
            await on_set_tracking(course_id_int, str(status or ""))

        async def _on_clear_tracking_status() -> None:
            await on_clear_tracking(course_id_int)

        def _on_tracking_changed(status: str) -> None:
            value = str(status or "").strip()
            if not value:
                state.tracking_by_course_id.pop(course_id_int, None)
                return
            state.tracking_by_course_id[course_id_int] = {"course_id": course_id_int, "status": value}

        await open_explore_course_details_dialog(
            course_id=course_id_int,
            focus_reviews=bool(focus),
            username=username,
            is_admin=is_admin,
            state_tracking_by_course_id=state.tracking_by_course_id,
            review_summary_by_course_id=state.course_review_summary_by_course_id,
            recommendation_summary_by_course_id=state.course_recommendation_summary_by_course_id,
            load_detail_bundle=lambda _cid, _scope: controller.load_course_detail_bundle(
                course_id=int(_cid),
                cache_scope=str(_scope or ""),
            ),
            save_review=lambda _cid, _rating, _text, _scope: controller.save_course_review(
                course_id=int(_cid),
                rating=int(_rating),
                text=str(_text or ""),
                cache_scope=str(_scope or ""),
            ),
            delete_review=lambda _cid, _review_id, _scope: controller.delete_course_review(
                course_id=int(_cid),
                review_id=int(_review_id),
                cache_scope=str(_scope or ""),
            ),
            on_set_tracking_status=_on_set_tracking_status,
            on_clear_tracking_status=_on_clear_tracking_status,
            on_tracking_changed=_on_tracking_changed,
            normalize_course_view_mode=normalize_course_view_mode,
            format_short_date=format_short_date,
        )

    async def _open_course_details(cid: int, focus: bool) -> None:
        _ = course_row
        await _open_explore_course_details(int(cid), bool(focus))

    async def _open_course_recommend(cid: int) -> None:
        ui.navigate.to(f"/courses?course_id={int(cid)}")

    async def _open_course_delete(cid: int) -> None:
        ui.navigate.to(f"/courses?course_id={int(cid)}")

    return build_course_card_actions(
        course_id=course_id,
        course_url=course_url,
        course_row=course_row,
        on_open_details=_open_course_details,
        on_open_recommend=_open_course_recommend,
        on_open_edit=lambda row: ui.navigate.to(f"/courses?course_id={int(row.get('id') or 0)}"),
        on_confirm_delete=_open_course_delete,
    )


async def open_explore_article_details(article_row: dict[str, Any], focus_reviews: bool) -> None:
    """Open article details dialog for Explore article cards."""
    open_explore_article_details_dialog(article_row=article_row, focus_reviews=bool(focus_reviews))
