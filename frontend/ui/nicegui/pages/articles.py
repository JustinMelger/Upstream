"""Articles (shared links) page for the NiceGUI frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


def _format_article_date(ts: str | None) -> str:
    """Format an ISO-8601 timestamp as `Mon DD, YYYY` for display."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return ts


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/articles` route."""

    @ui.page("/articles")
    async def articles_page() -> None:
        if await require_user(store, api) is None:
            return

        render_shell(title="Articles", store=store, api=api)

        articles: list[dict[str, Any]] = []
        loading = False

        async def _load() -> None:
            nonlocal articles, loading
            if loading:
                return
            loading = True
            refresh_btn.disable()
            meta.text = "Loading..."
            articles_list.refresh()
            try:
                params: dict[str, Any] = {}
                if q.value:
                    params["q"] = str(q.value)
                if tag.value:
                    params["tag"] = str(tag.value)
                articles = list(await api.get("/articles", params=params or None) or [])
                meta.text = f"{len(articles)} articles"
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                articles = []
                meta.text = "Failed to load"
            finally:
                loading = False
                refresh_btn.enable()
                articles_list.refresh()

        @guard_ui_action(title="Share article failed")
        async def _create() -> None:
            payload = {
                "title": str(new_title.value or ""),
                "url": str(new_url.value or ""),
                "tags": str(new_tags.value or ""),
            }
            await api.post("/articles", payload)
            ui.notify("Shared", type="positive")
            new_title.value = ""
            new_url.value = ""
            new_tags.value = ""
            await _load()

        with render_container():
            ui.label("Share useful resources with colleagues.").classes("text-sm text-gray-600")

            with ui.card().classes("lp-card w-full"):
                ui.label("Share an article").classes("text-lg font-semibold")
                new_title = ui.input("Title").props("clearable").classes("w-full")
                new_url = ui.input("URL").props("clearable").classes("w-full")
                new_tags = ui.input("Tags (comma separated)").props("clearable").classes("w-full")
                with ui.row().classes("justify-end mt-2"):
                    ui.button("Share", on_click=_create)

            ui.separator()

            with ui.row().classes("items-end w-full"):
                q = ui.input("Search").props("clearable debounce=400").classes("grow")
                tag = ui.input("Tag").props("clearable debounce=400")

            meta = ui.label("").classes("text-sm text-gray-600")

            @ui.refreshable
            def articles_list() -> None:
                with ui.column().classes("w-full gap-3"):
                    if loading:
                        render_card_skeletons(count=3)
                        return
                    if not articles:
                        ui.label("No articles yet.").classes("text-sm text-gray-600")
                        ui.label("Share the first link above.").classes("text-sm text-gray-600")
                        return

                    for a in list(articles):
                        with ui.card().classes("lp-card w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(str(a.get("title") or "")).classes("text-lg font-semibold")
                                    url = str(a.get("url") or "").strip()
                                    if url:
                                        ui.link(url, url).props("target=_blank").classes("text-sm")
                                    subtitle_bits = [
                                        str(a.get("created_by") or "").strip(),
                                        _format_article_date(str(a.get("created_at") or "").strip()),
                                    ]
                                    ui.label(" · ".join([b for b in subtitle_bits if b])).classes("text-sm text-gray-600")
                                    tags_s = str(a.get("tags") or "").strip()
                                    if tags_s:
                                        with ui.row().classes("items-center gap-2 flex-wrap"):
                                            for t in [x.strip() for x in tags_s.split(",") if x.strip()][:8]:
                                                ui.label(t).classes("lp-meta-chip")

            async def _on_filter_change(*_: Any) -> None:
                await _load()

            q.on("update:model-value", _on_filter_change)
            tag.on("update:model-value", _on_filter_change)

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load).props("outline")

            await _load()
            articles_list()
