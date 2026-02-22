"""Dialog builders/flows for the Articles page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags


def build_share_article_dialog(
    *,
    on_submit: Callable[[dict[str, Any]], Awaitable[None]],
    on_suggest_from_url: Callable[[str], Awaitable[dict[str, Any]]],
) -> Callable[[], None]:
    """Build share dialog and return open callback."""
    share_dialog = ui.dialog()
    with share_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label("Share article").classes("text-xl font-semibold")
        new_title = ui.input("Title").props("clearable").classes("w-full")
        new_url = ui.input("URL").props("clearable").classes("w-full")
        with ui.row().classes("items-center justify-between w-full -mt-2"):
            ui.label("Paste a link and auto-suggest title/tags.").classes("text-xs").style("color: var(--lp-muted)")

            @guard_ui_action(title="URL suggestion failed")
            async def _suggest_from_url() -> None:
                source_url = str(new_url.value or "").strip()
                if not source_url:
                    safe_notify("Enter a URL first", type="warning")
                    return
                payload = await on_suggest_from_url(source_url)
                suggested_title = str(payload.get("title") or "").strip()
                suggested_tags = list(payload.get("suggested_tags") or [])
                normalized_url = str(payload.get("normalized_url") or "").strip()
                if normalized_url:
                    new_url.value = normalized_url
                if suggested_title and not str(new_title.value or "").strip():
                    new_title.value = suggested_title
                if suggested_tags and not str(new_tags.value or "").strip():
                    new_tags.value = ", ".join([str(tag).strip() for tag in suggested_tags if str(tag).strip()])
                if suggested_title or suggested_tags:
                    safe_notify("Suggestions applied", type="positive")
                else:
                    safe_notify("No suggestions found for this URL", type="warning")

            ui.button("Suggest from URL", on_click=_suggest_from_url).props("outline dense")
        new_tags = ui.input("Tags (comma separated)").props("clearable").classes("w-full")
        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Share failed")
            async def _submit_share() -> None:
                payload = {
                    "title": str(new_title.value or ""),
                    "url": str(new_url.value or ""),
                    "tags": str(new_tags.value or ""),
                }
                await on_submit(payload)
                safe_notify("Shared", type="positive")
                share_dialog.close()

            ui.button("Share", on_click=_submit_share)
            ui.button("Cancel", on_click=share_dialog.close).props("outline")

    def _open_share_dialog() -> None:
        new_title.value = ""
        new_url.value = ""
        new_tags.value = ""
        share_dialog.open()

    return _open_share_dialog


async def open_article_details_dialog(
    *,
    article: dict[str, Any],
    focus_reviews: bool,
    username: str,
    is_admin: bool,
    load_reviews: Callable[[int], Awaitable[list[dict[str, Any]]]],
    save_review: Callable[[int, int, str], Awaitable[dict[str, Any]]],
    delete_review: Callable[[int, int], Awaitable[bool]],
    review_summary_by_article_id: dict[int, dict[str, Any]],
    format_review_summary: Callable[[dict[str, Any] | None], str],
    format_date: Callable[[Any], str],
) -> None:
    """Open article details/reviews dialog."""
    article_id = int(article.get("id") or 0)
    reviews = list(await load_reviews(int(article_id)) or [])

    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label(str(article.get("title") or "")).classes("text-xl font-semibold")
        if not focus_reviews:
            with ui.row().classes("items-center justify-between w-full mt-2"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    tags = parse_tags(str(article.get("tags") or ""))
                    for t in tags[:10]:
                        ui.label(t).classes("lp-meta-chip")
                    shared_by = str(article.get("created_by") or "").strip()
                    if shared_by:
                        ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                    summary = format_review_summary(review_summary_by_article_id.get(article_id))
                    if summary:
                        ui.label(f"★ {summary}").classes("lp-meta-chip")
                url = str(article.get("url") or "").strip()
                if url:
                    ui.button(
                        "Open link",
                        icon="open_in_new",
                        on_click=lambda u=url: ui.navigate.to(u, new_tab=True),
                    ).props("outline dense")
            ui.separator()

        def _sync_summary(current_reviews: list[dict[str, Any]]) -> None:
            ratings: list[int] = []
            for r in list(current_reviews or []):
                try:
                    ratings.append(int(r.get("rating") or 0))
                except (TypeError, ValueError):
                    continue
            if not ratings:
                review_summary_by_article_id[article_id] = {
                    "article_id": article_id,
                    "avg_rating": 0.0,
                    "review_count": 0,
                }
            else:
                avg = float(sum(ratings)) / float(len(ratings))
                review_summary_by_article_id[article_id] = {
                    "article_id": article_id,
                    "avg_rating": float(avg),
                    "review_count": int(len(ratings)),
                }

        async def _save_review(rating: int, text: str) -> dict[str, Any]:
            return await save_review(int(article_id), int(rating), str(text or ""))

        async def _delete_review(review_id: int) -> bool:
            return await delete_review(int(article_id), int(review_id))

        render_reviews_panel(
            username=username,
            is_admin=is_admin,
            reviews=reviews,
            section_title="Reviews",
            empty_text="No reviews yet.",
            on_save=_save_review,
            on_delete=_delete_review,
            format_date=format_date,
            on_changed=_sync_summary,
        )
        with ui.row().classes("justify-end mt-4"):
            ui.button("Close", on_click=dialog.close).props("outline")
    dialog.open()
