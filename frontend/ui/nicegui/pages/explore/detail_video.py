"""Video detail route renderer for Explore."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.learning_items import (
    learning_item_primary_action_label,
    learning_item_source_action_label,
)
from frontend.ui.nicegui.core.page_copy import PrimaryPage, subtitle_for
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.explore.detail_common import parse_detail_id, render_breadcrumb, render_detail_scope
from frontend.ui.nicegui.pages.videos.controller import VideosPageController


async def render_explore_video_detail_page(*, store: SessionStore, api: ApiClient, video_id: str) -> None:
    """Render dedicated Explore video detail route."""
    user = await require_user(store, api)
    if user is None:
        return
    vid = parse_detail_id(video_id)
    with render_detail_scope(store=store, api=api):
        with ui.row().classes("w-full items-center"):
            ui.label(subtitle_for(PrimaryPage.EXPLORE)).classes("text-sm text-gray-600")
        ui.element("div").classes("h-2")
        render_breadcrumb(label="Videos")
        if vid <= 0:
            ui.label("Invalid video id").classes("text-sm")
            return

        controller = VideosPageController(api=api)
        try:
            video = await controller.load_video(video_id=vid)
        except ApiError as exc:
            ui.label(f"Video unavailable ({exc.status_code})").classes("text-sm")
            return
        if not isinstance(video, dict) or int(video.get("id") or 0) != vid:
            ui.label("Video not found").classes("text-sm")
            return

        title = str(video.get("title") or "Video").strip()
        description = str(video.get("description") or "").strip()
        provider = str(video.get("provider") or "").strip()
        category = str(video.get("category") or "").strip()
        source_url = str(video.get("url") or "").strip()
        owner = str(video.get("created_by") or "").strip()
        with ui.row().classes("w-full items-start gap-4 lp-refresh-region"):
            with ui.column().classes("lp-explore-detail-main"):
                with ui.element("header").classes("lp-explore-detail-hero"):
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.label("Learning item").classes("lp-explore-detail-eyebrow")
                        ui.label("Video").classes("lp-meta-chip lp-meta-chip--quiet")
                    ui.label(title).classes("lp-explore-detail-title")
                    bits = [bit for bit in [provider, category, f"by {owner}" if owner else ""] if bit]
                    if bits:
                        ui.label(" · ".join(bits)).classes("lp-explore-detail-muted")
                    ui.label(description or "No description provided yet.").classes("lp-explore-detail-body")
                with ui.card().classes("lp-card w-full lp-explore-detail-card lp-explore-main-surface"):
                    if source_url:
                        ui.button(
                            learning_item_primary_action_label("video"),
                            icon="open_in_new",
                            on_click=lambda: ui.navigate.to(source_url, new_tab=True),
                        ).props("unelevated")
                    ui.label(description or "Open the source to continue learning.").classes("lp-explore-detail-muted")

            with ui.column().classes("lp-explore-detail-side lp-explore-info-card"):
                ui.label("Video Actions").classes("text-base font-semibold")
                if source_url:
                    ui.button(
                        learning_item_source_action_label("video"),
                        on_click=lambda: ui.navigate.to(source_url, new_tab=True),
                    ).props("outline")
                ui.button(
                    "Share learning item",
                    icon="share",
                    on_click=lambda: copy_text_to_clipboard(
                        text=source_url or f"/explore/videos/{vid}",
                        success_message=f"Video link copied: /explore/videos/{vid}",
                    ),
                ).props("outline")
