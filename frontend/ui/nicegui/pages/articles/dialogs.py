"""Dialog builders/flows for the Articles page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui
from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.suggestion_utils import suggestion_badge_text
from frontend.ui.nicegui.pages.articles.ui_glue import parse_tags


_HTTP_URL_ADAPTER: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def _normalize_http_url(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        return str(_HTTP_URL_ADAPTER.validate_python(value))
    except ValidationError:
        return ""


def build_share_article_dialog(
    *,
    username: str,
    on_submit: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    on_suggest_from_url: Callable[[str], Awaitable[dict[str, Any]]],
    is_duplicate_url: Callable[[str], bool] | None = None,
) -> Callable[[], None]:
    """Build share dialog and return open callback."""
    share_dialog = ui.dialog()
    with share_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
        ui.label("Share article").classes("text-xl font-semibold")
        new_title = ui.input("Title").props("clearable").classes("w-full")
        new_url = ui.input("URL").props("clearable").classes("w-full")
        title_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        url_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        auto_suggest_state: dict[str, int | str] = {"nonce": 0, "last_source": ""}
        auto_draft_state: dict[str, int | bool] = {"nonce": 0, "enabled": True}
        suggested_values: dict[str, str] = {}
        new_tags = ui.input("Tags (comma separated)").props("clearable").classes("w-full")
        tags_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        article_draft_key = f"articles_share_draft::{username}"

        def _article_draft_payload() -> dict[str, Any]:
            return {
                "title": str(new_title.value or ""),
                "url": str(new_url.value or ""),
                "tags": str(new_tags.value or ""),
            }

        def _draft_has_content(raw: Any) -> bool:
            if not isinstance(raw, dict):
                return False
            return any(str(v or "").strip() for v in raw.values())

        def _save_draft_silent() -> None:
            if not bool(auto_draft_state.get("enabled", True)):
                return
            app.storage.user[article_draft_key] = _article_draft_payload()

        def _queue_draft_autosave(*_args: Any) -> None:
            if not bool(auto_draft_state.get("enabled", True)):
                return
            next_nonce = int(auto_draft_state.get("nonce") or 0) + 1
            auto_draft_state["nonce"] = next_nonce

            async def _run() -> None:
                await asyncio.sleep(0.3)
                if next_nonce != int(auto_draft_state.get("nonce") or 0):
                    return
                _save_draft_silent()

            asyncio.create_task(_run())

        def _apply_draft(raw: Any) -> None:
            draft = raw if isinstance(raw, dict) else {}
            auto_draft_state["enabled"] = False
            new_title.value = str(draft.get("title") or "")
            new_url.value = str(draft.get("url") or "")
            new_tags.value = str(draft.get("tags") or "")
            suggested_values.clear()
            _refresh_url_hint()
            _refresh_suggestion_hints()
            auto_draft_state["enabled"] = True

        def _discard_draft(*, reset_form: bool, notify: bool) -> None:
            app.storage.user.pop(article_draft_key, None)
            if reset_form:
                _apply_draft({})
            if notify:
                safe_notify("Draft discarded", type="positive")

        def _refresh_suggestion_hints() -> None:
            title_suggest_hint.text = suggestion_badge_text(
                current_value=str(new_title.value or ""),
                suggested_value=str(suggested_values.get("title") or ""),
            )
            tags_suggest_hint.text = suggestion_badge_text(
                current_value=str(new_tags.value or ""),
                suggested_value=str(suggested_values.get("tags") or ""),
            )

        with ui.row().classes("items-center justify-between w-full -mt-2"):
            ui.label("Paste a link and auto-suggest title/tags.").classes("text-xs").style("color: var(--lp-muted)")

            def _refresh_url_hint() -> bool:
                normalized = _normalize_http_url(str(new_url.value or ""))
                if not str(new_url.value or "").strip():
                    url_hint.text = ""
                    return True
                if not normalized:
                    url_hint.text = "Enter a valid http(s) URL."
                    return False
                if is_duplicate_url is not None and is_duplicate_url(normalized):
                    url_hint.text = "Similar URL already exists in the article stream."
                    return True
                url_hint.text = "URL looks good."
                return True

            async def _suggest_from_url(*, auto_trigger: bool = False) -> None:
                source_url = str(new_url.value or "").strip()
                if not source_url:
                    if not auto_trigger:
                        safe_notify("Enter a URL first", type="warning")
                    return
                if auto_trigger and source_url == str(auto_suggest_state.get("last_source") or ""):
                    return
                payload = await on_suggest_from_url(source_url)
                suggested_title = str(payload.get("title") or "").strip()
                suggested_tags = list(payload.get("suggested_tags") or [])
                normalized_url = str(payload.get("normalized_url") or "").strip()
                if normalized_url:
                    new_url.value = normalized_url
                if suggested_title and not str(new_title.value or "").strip():
                    new_title.value = suggested_title
                    suggested_values["title"] = suggested_title
                if suggested_tags and not str(new_tags.value or "").strip():
                    new_tags.value = ", ".join([str(tag).strip() for tag in suggested_tags if str(tag).strip()])
                    suggested_values["tags"] = str(new_tags.value or "")
                if suggested_title or suggested_tags:
                    safe_notify("Suggestions applied", type="positive")
                else:
                    safe_notify("No suggestions found for this URL", type="warning")
                auto_suggest_state["last_source"] = normalized_url or source_url
                _refresh_url_hint()
                _refresh_suggestion_hints()

            @guard_ui_action(title="URL suggestion failed")
            async def _suggest_from_url_manual() -> None:
                await _suggest_from_url(auto_trigger=False)

            async def _suggest_from_url_auto() -> None:
                await _suggest_from_url(auto_trigger=True)

            def _queue_auto_suggest(*_args: Any) -> None:
                next_nonce = int(auto_suggest_state.get("nonce") or 0) + 1
                auto_suggest_state["nonce"] = next_nonce

                async def _run() -> None:
                    await asyncio.sleep(0.35)
                    if next_nonce != int(auto_suggest_state.get("nonce") or 0):
                        return
                    await _suggest_from_url_auto()

                asyncio.create_task(_run())

            new_url.on("blur", _queue_auto_suggest)
            new_url.on("paste", _queue_auto_suggest)
            new_url.on("update:model-value", lambda *_: _refresh_url_hint())
            new_title.on("update:model-value", lambda *_: _refresh_suggestion_hints())
            new_tags.on("update:model-value", lambda *_: _refresh_suggestion_hints())

            ui.button("Suggest from URL", on_click=_suggest_from_url_manual).props("outline dense")

        def _open_success_summary(*, created_row: dict[str, Any], autofilled_fields: list[str]) -> None:
            title = str(created_row.get("title") or "Article")
            source_url = str(created_row.get("url") or "").strip()

            def _share_another(summary_dialog: Any) -> None:
                summary_dialog.close()
                suggested_values.clear()
                _refresh_suggestion_hints()
                _open_share_dialog()

            with ui.dialog() as summary_dialog, ui.card().classes("lp-card lp-dialog w-[min(620px,95vw)]"):
                ui.label("Article shared").classes("text-lg font-semibold")
                ui.label(f"{title} is now visible in the article stream.").classes("text-sm").style(
                    "color: var(--lp-muted)"
                )
                if autofilled_fields:
                    ui.label("Autofilled fields: " + ", ".join(autofilled_fields)).classes("text-xs").style(
                        "color: var(--lp-muted)"
                    )
                with ui.row().classes("justify-end mt-4 gap-2"):
                    if source_url:
                        ui.button("Open source", on_click=lambda u=source_url: ui.navigate.to(str(u), new_tab=True)).props("outline")
                        ui.button(
                            "Copy link",
                            on_click=lambda u=source_url: copy_text_to_clipboard(text=str(u)),
                        ).props("outline")
                    ui.button(
                        "Share another",
                        on_click=lambda d=summary_dialog: _share_another(d),
                    )
                    ui.button("Done", on_click=summary_dialog.close).props("outline")
            summary_dialog.open()

        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Share failed")
            async def _submit_share() -> None:
                if not _refresh_url_hint():
                    safe_notify("Enter a valid URL before sharing", type="negative")
                    return
                payload = {
                    "title": str(new_title.value or ""),
                    "url": str(new_url.value or ""),
                    "tags": str(new_tags.value or ""),
                }
                created_row = dict(await on_submit(payload) or {})
                _discard_draft(reset_form=False, notify=False)
                share_dialog.close()
                autofilled_fields: list[str] = []
                if suggestion_badge_text(
                    current_value=str(payload.get("title") or ""),
                    suggested_value=str(suggested_values.get("title") or ""),
                ) == "Suggested":
                    autofilled_fields.append("Title")
                if suggestion_badge_text(
                    current_value=str(payload.get("tags") or ""),
                    suggested_value=str(suggested_values.get("tags") or ""),
                ) == "Suggested":
                    autofilled_fields.append("Tags")
                _open_success_summary(created_row=created_row, autofilled_fields=autofilled_fields)

            ui.button("Discard draft", on_click=lambda: _discard_draft(reset_form=True, notify=True)).props("outline")
            ui.button("Share", on_click=_submit_share)
            ui.button("Cancel", on_click=share_dialog.close).props("outline")

        new_title.on("update:model-value", _queue_draft_autosave)
        new_url.on("update:model-value", _queue_draft_autosave)
        new_tags.on("update:model-value", _queue_draft_autosave)

    def _open_share_dialog() -> None:
        draft = app.storage.user.get(article_draft_key)
        _apply_draft(draft)
        if _draft_has_content(draft):
            safe_notify("Recovered unsent draft", type="positive")
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
