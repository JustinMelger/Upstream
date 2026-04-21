"""Article detail route renderer for Explore."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.learning_items import (
    learning_item_primary_action_label,
    learning_item_source_action_label,
)
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.courses.ui_glue import format_short_date
from frontend.ui.nicegui.pages.explore.detail_common import parse_detail_id, render_breadcrumb, render_detail_scope


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _avg_rating(*, reviews: list[dict[str, Any]]) -> tuple[float, int]:
    ratings: list[int] = []
    for row in reviews:
        rating = _safe_int(row.get("rating"))
        if 1 <= rating <= 5:
            ratings.append(rating)
    if not ratings:
        return 0.0, 0
    return float(sum(ratings)) / float(len(ratings)), len(ratings)


def _stars(*, avg: float) -> str:
    rounded = max(0, min(5, int(round(float(avg)))))
    return ("★" * rounded) + ("☆" * (5 - rounded))


def _render_article_main_panel(
    *,
    controller: ArticlesPageController,
    aid: int,
    username: str,
    is_admin: bool,
    article: dict[str, Any],
    reviews: list[dict[str, Any]],
    tags: list[str],
) -> None:
    avg_rating, review_count = _avg_rating(reviews=reviews)

    with ui.column().classes("lp-explore-detail-main"):
        with ui.element("header").classes("lp-explore-detail-hero"):
            owner = str(article.get("created_by") or "").strip()
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.label("Learning item").classes("lp-explore-detail-eyebrow")
                ui.label("Article").classes("lp-meta-chip lp-meta-chip--quiet")
            ui.label(str(article.get("title") or "Article")).classes("lp-explore-detail-title")
            if owner:
                ui.label(f"by {owner}").classes("lp-explore-detail-muted")
            summary = str(article.get("summary") or "").strip()
            if summary:
                ui.label(summary).classes("lp-explore-detail-body")

        with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface"):
            with ui.row().classes("items-center gap-2 flex-wrap lp-explore-detail-meta-row"):
                for tag in tags[:6]:
                    ui.label(tag).classes("lp-meta-chip")

            body = str(article.get("content") or article.get("summary") or "").strip()
            ui.label(body or "No content available yet.").classes("lp-explore-detail-muted")

        with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface lp-explore-reviews-panel"):
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                if review_count > 0:
                    ui.label(_stars(avg=avg_rating)).classes("lp-explore-rating-stars")
                    ui.label(f"{avg_rating:.1f}").classes("lp-explore-rating-score")
                    ui.label(f"{review_count} review{'s' if review_count != 1 else ''}").classes(
                        "lp-explore-detail-muted"
                    )
                else:
                    ui.label("No reviews yet").classes("lp-explore-detail-muted")
            render_reviews_panel(
                username=username,
                is_admin=is_admin,
                reviews=reviews,
                on_save=lambda rating, text: controller.save_article_review(
                    article_id=aid,
                    rating=int(rating),
                    text=str(text or ""),
                ),
                on_delete=lambda review_id: controller.delete_article_review(
                    article_id=aid,
                    review_id=int(review_id),
                ),
                hooks=ReviewPanelHooks(format_date=format_short_date),
            )


def _render_article_info_panel(*, aid: int, article: dict[str, Any], tags: list[str], source_url: str) -> None:
    with ui.column().classes("lp-explore-detail-side lp-explore-info-card"):
        ui.label("Article Actions").classes("text-base font-semibold")

        if source_url:
            ui.button(
                learning_item_primary_action_label("article"),
                icon="open_in_new",
                on_click=lambda: ui.navigate.to(source_url, new_tab=True),
            ).props("unelevated")
            ui.button(
                learning_item_source_action_label("article"),
                on_click=lambda: ui.navigate.to(source_url, new_tab=True),
            ).props("outline")

        ui.button(
            "Share learning item",
            icon="share",
            on_click=lambda: copy_text_to_clipboard(
                text=source_url or f"/explore/articles/{aid}",
                success_message=f"Article link copied: /explore/articles/{aid}",
            ),
        ).props("outline")

        ui.separator()
        ui.label("Resources").classes("text-sm font-semibold")
        if source_url:
            ui.link(learning_item_source_action_label("article"), source_url).classes("lp-explore-detail-muted")
        for tag in tags[:6]:
            ui.label(tag).classes("lp-explore-detail-muted")


async def render_explore_article_detail_page(*, store: SessionStore, api: ApiClient, article_id: str) -> None:
    """Render dedicated Explore article detail route."""
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    is_admin = str(user.get("role") or "") == "admin"
    aid = parse_detail_id(article_id)

    with render_detail_scope(store=store, api=api):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        ui.element("div").classes("h-2")
        render_breadcrumb(label="Articles")
        if aid <= 0:
            ui.label("Invalid article id").classes("text-sm")
            return

        controller = ArticlesPageController(api=api)
        try:
            bundle = await controller.load_list_bundle()
        except ApiError as exc:
            ui.label(f"Article unavailable ({exc.status_code})").classes("text-sm")
            return

        article = next((a for a in bundle.articles if int(a.get("id") or 0) == aid), None)
        if not isinstance(article, dict):
            ui.label("Article not found").classes("text-sm")
            return

        reviews = await controller.load_article_reviews(article_id=aid)
        source_url = str(article.get("url") or "").strip()
        tags = parse_tags(str(article.get("tags") or ""))

        with ui.row().classes("w-full items-start gap-4 lp-refresh-region"):
            _render_article_main_panel(
                controller=controller,
                aid=aid,
                username=username,
                is_admin=is_admin,
                article=article,
                reviews=reviews,
                tags=tags,
            )
            _render_article_info_panel(
                aid=aid,
                article=article,
                tags=tags,
                source_url=source_url,
            )
