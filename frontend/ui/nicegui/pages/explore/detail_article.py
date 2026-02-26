"""Article detail route renderer for Explore."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.articles.controller import ArticlesPageController
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags
from frontend.ui.nicegui.pages.courses.ui_glue import format_short_date
from frontend.ui.nicegui.pages.explore.detail_common import parse_detail_id, render_breadcrumb, render_detail_scope


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
        url = str(article.get("url") or "").strip()
        tags = parse_tags(str(article.get("tags") or ""))

        with ui.row().classes("w-full items-start gap-4"):
            with ui.column().classes("lp-explore-detail-main"):
                ui.label(str(article.get("title") or "Article")).classes("lp-explore-detail-title")
                if str(article.get("summary") or "").strip():
                    ui.label(str(article.get("summary") or "")).classes("lp-explore-detail-body")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    if str(article.get("created_by") or "").strip():
                        ui.label(f"Shared by {article.get('created_by')}").classes("lp-meta-chip lp-meta-chip--quiet")
                    for tag in tags[:6]:
                        ui.label(tag).classes("lp-meta-chip")
                render_reviews_panel(
                    username=username,
                    is_admin=is_admin,
                    reviews=reviews,
                    on_save=lambda rating, text: controller.save_article_review(
                        article_id=aid,
                        rating=int(rating),
                        text=str(text or ""),
                    ),
                    on_delete=lambda review_id: controller.delete_article_review(article_id=aid, review_id=int(review_id)),
                    hooks=ReviewPanelHooks(format_date=format_short_date),
                )

            with ui.column().classes("lp-explore-detail-side"):
                ui.label("Actions").classes("text-sm font-semibold")
                if url:
                    ui.button("Open source", on_click=lambda: ui.navigate.to(url, new_tab=True)).props("outline")
