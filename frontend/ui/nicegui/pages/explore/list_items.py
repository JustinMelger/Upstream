"""Item-level render helpers for Explore list sections."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.learning_items import learning_item_type_label
from frontend.ui.nicegui.core.path_items import count_course_items
from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.domains.articles.actions import build_article_card_actions
from frontend.ui.nicegui.domains.courses.media import (
    extract_youtube_video_id,
    preferred_card_image_url,
    youtube_thumbnail_url,
)
from frontend.ui.nicegui.domains.courses.ui_glue import normalize_course_tracking_status


def _render_browse_row(
    *,
    icon: str,
    title: str,
    subtitle: str,
    meta: str,
    image_url: str = "",
    primary_label: str,
    on_primary: Callable[[], Any],
    secondary_label: str | None = None,
    on_secondary: Callable[[], Any] | None = None,
) -> None:
    """Render one simplified Explore browse row."""
    with ui.card().classes("w-full lp-card lp-explore-row-card"):
        with ui.row().classes("w-full items-center gap-4 no-wrap"):
            if str(image_url or "").strip():
                with ui.element("div").classes("lp-explore-row-thumb"):
                    ui.image(str(image_url)).classes("lp-explore-row-thumb-img")
            else:
                with ui.element("div").classes("lp-explore-row-icon"):
                    ui.icon(icon).classes("text-lg")
            with ui.column().classes("gap-1 min-w-0 flex-1"):
                ui.label(str(title or "Untitled")).classes("lp-explore-row-title")
                if str(subtitle or "").strip():
                    ui.label(str(subtitle)).classes("lp-explore-row-subtitle")
                if str(meta or "").strip():
                    ui.label(str(meta)).classes("lp-explore-row-meta")
            with ui.row().classes("items-center justify-end gap-2 lp-explore-row-actions"):
                if secondary_label and on_secondary is not None:
                    ui.button(str(secondary_label), on_click=on_secondary).props("outline color=primary")
                ui.button(str(primary_label), on_click=on_primary).props("unelevated color=primary")


def _resolve_row_image_url(*, row: dict[str, Any], kind: str) -> str:
    """Resolve a compact preview image URL for Explore rows."""
    source_url = str(row.get("url") or "").strip()
    payload_image = preferred_card_image_url(
        image_url=row.get("preview_image_url"),
        source_url=source_url,
        allow_favicon_fallback=kind not in {"course", "video"},
    )
    if payload_image:
        return payload_image

    if not source_url:
        return ""

    if kind in {"course", "video"}:
        video_id = extract_youtube_video_id(source_url)
        if video_id:
            return youtube_thumbnail_url(video_id)
    return ""


def render_course_item(
    *,
    course: dict[str, Any],
    item_classes: str,
    state: Any,
    username: str,
    is_admin: bool,
    course_actions_builder: Callable[[dict[str, Any], int, str], Any],
    item_type: str,
    on_set_tracking: Callable[[int, str], Awaitable[None]],
    on_clear_tracking: Callable[[int], Awaitable[None]],
) -> None:
    """Render one course row item for Explore."""
    with ui.element("div").classes(item_classes):
        _ = username
        _ = is_admin
        _ = on_set_tracking
        _ = on_clear_tracking
        course_id = int(course.get("id") or 0)
        tracked = state.tracking_by_course_id.get(course_id)
        url = str(course.get("url") or "").strip()
        actions = course_actions_builder(course, course_id, url)
        tracked_row = tracked if isinstance(tracked, dict) else None
        status_text = (
            normalize_course_tracking_status(tracked_row.get("status")).replace("_", " ").title() if tracked_row else ""
        )
        provider = str(course.get("provider") or "").strip()
        review_summary = format_review_summary(
            state.course_review_summary_by_course_id.get(course_id),
            style="star",
        )
        subtitle_parts = [part for part in [provider, status_text] if part]
        subtitle = " · ".join(subtitle_parts) if subtitle_parts else learning_item_type_label(item_type)
        meta_parts = [review_summary] if review_summary else ["No reviews yet"]
        created_by = str(course.get("created_by") or "").strip()
        if created_by:
            meta_parts.append(f"Shared by {created_by}")
        _render_browse_row(
            icon="school",
            title=str(course.get("title") or ""),
            subtitle=subtitle,
            meta=" · ".join(meta_parts),
            image_url=_resolve_row_image_url(row=course, kind="course"),
            primary_label="Open details",
            on_primary=actions.on_view,
            secondary_label="Review",
            on_secondary=actions.on_review,
        )


def render_path_item(
    *,
    path: dict[str, Any],
    item_classes: str,
    state: Any,
    username: str,
    is_admin: bool,
    on_toggle_path_selection: Callable[[int], Awaitable[None]],
    open_path: Callable[[int], None],
) -> None:
    """Render one path row item for Explore."""
    with ui.element("div").classes(item_classes):
        path_id = int(path.get("id") or 0)
        is_tracked = path_id in state.selected_by_path_id
        _ = on_toggle_path_selection
        _ = username
        _ = is_admin
        detail = state.selected_detail_by_path_id.get(path_id) or {}
        raw_course_ids = path.get("course_ids")
        inferred_total = 0
        if isinstance(raw_course_ids, list):
            inferred_total = len(raw_course_ids)
        else:
            try:
                inferred_total = int(path.get("course_count") or 0)
            except (TypeError, ValueError):
                inferred_total = 0
        tracked_total = count_course_items(detail=detail) if is_tracked else 0
        total_courses = tracked_total if (is_tracked and tracked_total > 0) else max(0, inferred_total)
        if total_courses <= 0 and isinstance(detail, dict):
            total_courses = count_course_items(detail=detail)

        def _open_path_reviews() -> None:
            ui.navigate.to(f"/explore/paths/{path_id}?view=reviews")

        review_summary = format_review_summary(state.path_review_summary_by_id.get(path_id), style="star")
        progress_text = (
            f"{0 if not is_tracked else max(0, int(detail.get('completed_count') or 0))} / {max(0, total_courses)} courses"
        )
        subtitle_parts = [progress_text]
        if is_tracked:
            subtitle_parts.append("Selected")
        _render_browse_row(
            icon="route",
            title=str(path.get("name") or path.get("title") or ""),
            subtitle=" · ".join(subtitle_parts),
            meta=review_summary or "No reviews yet",
            primary_label="Open details",
            on_primary=lambda: open_path(path_id),
            secondary_label="Review",
            on_secondary=_open_path_reviews,
        )


def render_article_item(
    *,
    article: dict[str, Any],
    item_classes: str,
    state: Any,
    open_article_details: Callable[[dict[str, Any], bool], Awaitable[None]],
) -> None:
    """Render one article row item for Explore."""
    with ui.element("div").classes(item_classes):
        article_id = int(article.get("id") or 0)
        actions = build_article_card_actions(
            article_row=article,
            on_open_details=open_article_details,
        )
        review_summary = format_review_summary(state.article_review_summary_by_article_id.get(article_id), style="star")
        author = str(article.get("created_by") or "").strip()
        tags = str(article.get("tags") or "").strip()
        subtitle_parts = ["Article"]
        if author:
            subtitle_parts.append(f"Shared by {author}")
        _render_browse_row(
            icon="article",
            title=str(article.get("title") or ""),
            subtitle=" · ".join(subtitle_parts),
            meta=review_summary or tags,
            image_url=_resolve_row_image_url(row=article, kind="article"),
            primary_label="Open details",
            on_primary=actions.on_view,
            secondary_label="Review",
            on_secondary=actions.on_review,
        )


def render_video_item(
    *,
    video: dict[str, Any],
    item_classes: str,
    state: Any,
) -> None:
    """Render one video row item for Explore."""
    with ui.element("div").classes(item_classes):
        video_id = int(video.get("id") or 0)
        provider = str(video.get("provider") or "").strip()
        created_by = str(video.get("created_by") or "").strip()
        review_summary = format_review_summary(state.video_review_summary_by_video_id.get(video_id), style="star")
        subtitle_parts = ["Video"]
        if provider:
            subtitle_parts.append(provider)
        if created_by:
            subtitle_parts.append(f"Shared by {created_by}")
        _render_browse_row(
            icon="smart_display",
            title=str(video.get("title") or ""),
            subtitle=" · ".join(subtitle_parts),
            meta=review_summary or "No reviews yet",
            image_url=_resolve_row_image_url(row=video, kind="video"),
            primary_label="Open details",
            on_primary=lambda: ui.navigate.to(f"/explore/videos/{video_id}"),
            secondary_label="Review",
            on_secondary=lambda: ui.navigate.to(f"/explore/videos/{video_id}?view=reviews"),
        )
