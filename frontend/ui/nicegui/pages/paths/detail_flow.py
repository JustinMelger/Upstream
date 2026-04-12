"""Detail dialog flow for the Paths page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.path_detail_sections import (
    PathDetailLearningView,
    render_path_detail_header,
    render_path_detail_learning_section,
)
from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks, ReviewPanelText
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.state import PathsPageState
from frontend.ui.nicegui.pages.paths.view_model import (
    compute_outcomes,
    format_review_summary,
    path_tracking_label,
    summarize_path_reviews,
)


def _normalize_view_mode(view_mode: str | None) -> str:
    return "reviews" if str(view_mode or "").strip().lower() == "reviews" else "full"


async def open_path_details_dialog(
    *,
    path_id: int,
    view_mode: str,
    controller: PathsPageController,
    state: PathsPageState,
    username: str,
    is_admin: bool,
    on_paths_refresh: Any,
) -> None:
    """Open and bind the path details dialog."""
    bundle = await controller.load_path_detail_bundle(path_id=int(path_id))
    detail = dict(bundle.detail or {})
    normalized_view_mode = _normalize_view_mode(view_mode)
    path_reviews: list[dict[str, Any]] = list(bundle.path_reviews or [])
    item_rows = list((detail.get("items") or []) if isinstance(detail, dict) else [])
    outcomes = compute_outcomes(
        detail=detail if isinstance(detail, dict) else {},
        tracking_by_course_id=state.tracking_by_course_id,
    )
    completed = int(outcomes.get("completed") or 0)
    total_courses = int(outcomes.get("total") or 0)
    progress = float(outcomes.get("ratio") or 0.0)

    review_summary_by_course_id: dict[int, dict[str, Any]] = dict(bundle.course_review_summary_by_course_id or {})
    item_rows = _enrich_path_items(
        items=item_rows,
        review_summary_by_course_id=review_summary_by_course_id,
        tracking_by_course_id=state.tracking_by_course_id,
    )

    next_course: dict[str, Any] | None = outcomes.get("next_course") if isinstance(outcomes, dict) else None

    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
        summary = format_review_summary(state.path_review_summary_by_id.get(int(path_id)))
        latest_activity = ""
        for row in path_reviews:
            created_at = str(row.get("created_at") or "").strip()
            if created_at:
                latest_activity = max(latest_activity, created_at[:10])
        render_path_detail_header(
            name=str(detail.get("name") or ""),
            description=str(detail.get("description") or ""),
            review_summary=summary,
            latest_activity=latest_activity,
        )
        if normalized_view_mode != "reviews":
            is_tracked = int(path_id) in state.selected_by_id

            @guard_ui_action(title="Open next course failed")
            async def _open_next() -> None:
                if next_course is None:
                    return
                url = str(next_course.get("url") or "").strip()
                if url:
                    ui.navigate.to(url, new_tab=True)
                    return
                safe_notify("Next course has no URL yet", type="warning")

            render_path_detail_learning_section(
                view=PathDetailLearningView(
                    total_courses=total_courses,
                    completed=completed,
                    progress=progress,
                    milestone=str(outcomes.get("milestone") or ""),
                    milestone_class=str(outcomes.get("milestone_class") or ""),
                    impact=str(outcomes.get("impact") or ""),
                    is_tracked=is_tracked,
                    tracking_label_text=path_tracking_label(is_tracked),
                    next_title=str(next_course.get("title") or "").strip() if isinstance(next_course, dict) else "",
                    item_rows=item_rows,
                ),
                on_open_next=_open_next if isinstance(next_course, dict) else None,
            )

        ui.separator().classes("my-2")

        def _sync_path_summary(current_reviews: list[dict[str, Any]]) -> None:
            state.path_review_summary_by_id[int(path_id)] = summarize_path_reviews(
                path_id=int(path_id),
                reviews=current_reviews,
            )
            on_paths_refresh()

        async def _save_path_review(rating: int, text: str) -> dict[str, Any]:
            return await controller.save_path_review(path_id=int(path_id), rating=int(rating), text=str(text or ""))

        async def _delete_path_review(review_id: int) -> bool:
            return await controller.delete_path_review(path_id=int(path_id), review_id=int(review_id))

        render_reviews_panel(
            username=username,
            is_admin=is_admin,
            reviews=path_reviews,
            on_save=_save_path_review,
            on_delete=_delete_path_review,
            text=ReviewPanelText(
                section_title="Path reviews",
                empty_text="No path reviews yet.",
            ),
            hooks=ReviewPanelHooks(on_changed=_sync_path_summary),
        )

        with ui.row().classes("justify-end mt-4"):
            ui.button("Close", on_click=dialog.close).props("outline")

    dialog.open()


def _enrich_path_items(
    *,
    items: list[dict[str, Any]],
    review_summary_by_course_id: dict[int, dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add tracking/review display data to mixed path learning items."""
    rows: list[dict[str, Any]] = []
    for row in items:
        enriched = dict(row)
        item_type = str(enriched.get("type") or "course").strip().lower()
        if item_type != "course":
            rows.append(enriched)
            continue
        try:
            course_id = int(enriched.get("id") or 0)
        except (TypeError, ValueError):
            rows.append(enriched)
            continue
        if course_id > 0:
            review_summary = review_summary_by_course_id.get(course_id) or {}
            review_count = int(review_summary.get("review_count") or 0)
            avg_rating = float(review_summary.get("avg_rating") or 0.0)
            if review_count > 0 and avg_rating > 0:
                enriched["reviews"] = f"{avg_rating:.1f}★ · {review_count} review{'s' if review_count != 1 else ''}"
            tracking = tracking_by_course_id.get(course_id) or {}
            enriched["tracking_status"] = str(tracking.get("status") or "")
        rows.append(enriched)
    return rows
