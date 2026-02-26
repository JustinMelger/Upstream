"""Dialog builders/flows for the Articles page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui
from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel, ReviewPanelHooks
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.metadata_fallback import build_article_metadata_fallback
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


def build_share_article_dialog(  # noqa: C901, PLR0915
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
        latest_suggestions: dict[str, str] = {}
        fallback_examples: dict[str, str] = {}
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
            latest_suggestions.clear()
            fallback_examples.clear()
            _refresh_url_hint()
            _refresh_suggestion_hints()
            _refresh_fallback_hint()
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

        fallback_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")

        def _refresh_fallback_hint() -> None:
            if not fallback_examples:
                fallback_hint.text = ""
                return
            fallback_hint.text = (
                "Metadata unavailable. Example values ready: "
                f"title='{fallback_examples.get('title', '')}', "
                f"tags='{fallback_examples.get('tags', '')}'."
            )

        def _cache_suggestion(*, key: str, value: str) -> None:
            cleaned = str(value or "").strip()
            if cleaned:
                latest_suggestions[key] = cleaned
            else:
                latest_suggestions.pop(key, None)

        def _apply_suggested_field(*, key: str, only_if_empty: bool) -> bool:
            value = str(latest_suggestions.get(key) or "").strip()
            if not value:
                return False
            if key == "title":
                if only_if_empty and str(new_title.value or "").strip():
                    return False
                new_title.value = value
                suggested_values["title"] = value
                return True
            if key == "tags":
                if only_if_empty and str(new_tags.value or "").strip():
                    return False
                new_tags.value = value
                suggested_values["tags"] = value
                return True
            return False

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
                suggested_tags_text = ", ".join([str(tag).strip() for tag in suggested_tags if str(tag).strip()])
                _cache_suggestion(key="title", value=suggested_title)
                _cache_suggestion(key="tags", value=suggested_tags_text)
                has_suggestions = bool(suggested_title or suggested_tags_text)
                fallback_examples.clear()
                if not has_suggestions:
                    fallback_examples.update(build_article_metadata_fallback(url=normalized_url or source_url))
                _refresh_fallback_hint()
                if normalized_url:
                    new_url.value = normalized_url
                _apply_suggested_field(key="title", only_if_empty=True)
                _apply_suggested_field(key="tags", only_if_empty=True)
                if has_suggestions:
                    safe_notify("Suggestions applied", type="positive")
                else:
                    safe_notify("No suggestions found for this URL", type="warning")
                auto_suggest_state["last_source"] = normalized_url or source_url
                _refresh_url_hint()
                _refresh_suggestion_hints()

            def _apply_fallback_examples() -> None:
                if not fallback_examples:
                    safe_notify("No fallback examples available", type="warning")
                    return
                changed = False
                title_example = str(fallback_examples.get("title") or "").strip()
                tags_example = str(fallback_examples.get("tags") or "").strip()
                if title_example and not str(new_title.value or "").strip():
                    new_title.value = title_example
                    changed = True
                if tags_example and not str(new_tags.value or "").strip():
                    new_tags.value = tags_example
                    changed = True
                _refresh_suggestion_hints()
                _save_draft_silent()
                if changed:
                    safe_notify("Fallback examples applied", type="positive")
                else:
                    safe_notify("Fallback examples are already filled", type="warning")

            @guard_ui_action(title="URL suggestion failed")
            async def _suggest_from_url_manual() -> None:
                await _suggest_from_url(auto_trigger=False)

            @guard_ui_action(title="Suggestion apply failed")
            async def _apply_all_suggestions() -> None:
                if not latest_suggestions:
                    await _suggest_from_url(auto_trigger=False)
                changed = _apply_suggested_field(key="title", only_if_empty=False)
                changed = _apply_suggested_field(key="tags", only_if_empty=False) or changed
                _refresh_suggestion_hints()
                _save_draft_silent()
                if changed:
                    safe_notify("All suggestions applied", type="positive")
                elif latest_suggestions:
                    safe_notify("No additional suggestions to apply", type="warning")

            @guard_ui_action(title="Suggestion apply failed")
            async def _resuggest_field(field_key: str, field_label: str) -> None:
                if field_key not in latest_suggestions:
                    await _suggest_from_url(auto_trigger=False)
                changed = _apply_suggested_field(key=field_key, only_if_empty=False)
                _refresh_suggestion_hints()
                _save_draft_silent()
                if changed:
                    safe_notify(f"{field_label} updated from suggestion", type="positive")
                else:
                    safe_notify(f"No suggestion available for {field_label.lower()}", type="warning")

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

            with ui.row().classes("items-center gap-2"):
                ui.button("Suggest from URL", on_click=_suggest_from_url_manual).props("outline dense")
                ui.button("Apply all suggestions", on_click=_apply_all_suggestions).props("outline dense")
                ui.button("Use fallback examples", on_click=_apply_fallback_examples).props("outline dense")
            with ui.row().classes("items-center gap-2"):
                ui.button("Re-suggest title", on_click=lambda: _resuggest_field("title", "Title")).props("flat dense")
                ui.button("Re-suggest tags", on_click=lambda: _resuggest_field("tags", "Tags")).props("flat dense")
            _refresh_fallback_hint()

        def _open_success_summary(*, created_row: dict[str, Any], autofilled_fields: list[str]) -> None:
            title = str(created_row.get("title") or "Article")
            source_url = str(created_row.get("url") or "").strip()

            def _share_another(summary_dialog: Any) -> None:
                summary_dialog.close()
                suggested_values.clear()
                latest_suggestions.clear()
                _refresh_suggestion_hints()
                _open_share_dialog()

            with ui.dialog() as summary_dialog, ui.card().classes("lp-card lp-dialog w-[min(620px,95vw)]"):
                ui.label("Article shared").classes("text-lg font-semibold")
                ui.label(f"{title} is now visible in the article stream.").classes("text-sm").style("color: var(--lp-muted)")
                if autofilled_fields:
                    ui.label("Autofilled fields: " + ", ".join(autofilled_fields)).classes("text-xs").style(
                        "color: var(--lp-muted)"
                    )
                with ui.row().classes("justify-end mt-4 gap-2"):
                    if source_url:
                        ui.button("Open source", on_click=lambda u=source_url: ui.navigate.to(str(u), new_tab=True)).props(
                            "outline"
                        )
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
                if (
                    suggestion_badge_text(
                        current_value=str(payload.get("title") or ""),
                        suggested_value=str(suggested_values.get("title") or ""),
                    )
                    == "Suggested"
                ):
                    autofilled_fields.append("Title")
                if (
                    suggestion_badge_text(
                        current_value=str(payload.get("tags") or ""),
                        suggested_value=str(suggested_values.get("tags") or ""),
                    )
                    == "Suggested"
                ):
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
        _refresh_fallback_hint()
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
                        "Open source",
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
            on_save=_save_review,
            on_delete=_delete_review,
            hooks=ReviewPanelHooks(
                format_date=format_date,
                on_changed=_sync_summary,
            ),
        )
        with ui.row().classes("justify-end mt-4"):
            ui.button("Close", on_click=dialog.close).props("outline")
    dialog.open()
