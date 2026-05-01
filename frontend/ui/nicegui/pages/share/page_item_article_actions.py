"""Article action wiring for learning-item share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.helpers import complete_share_publish, normalize_requested_share_type
from frontend.ui.nicegui.pages.share.page_item_drafts import refresh_detected_type_hint
from frontend.ui.nicegui.pages.share.page_item_form import ArticleShareControls, normalize_http_url
from frontend.ui.nicegui.pages.share.state import ShareArticleUiState


def wire_article_actions(
    *,
    controls: ArticleShareControls,
    state: ShareArticleUiState,
    controller: SharePageController,
    draft_key: str,
    app_module: Any,
    ui_module: Any,
    notify: Any,
) -> None:
    """Bind import/publish behavior for article share routes."""

    @guard_ui_action(title="Import failed")
    async def _import_metadata() -> None:
        raw_url = str(controls.url_input.value or "").strip()
        normalized = normalize_http_url(raw_url)
        if not normalized:
            controls.url_hint.text = "Enter a valid http(s) URL."
            controls.url_hint.update()
            notify("Enter a valid URL first", type="negative")
            return
        controls.url_input.value = normalized
        controls.url_hint.text = "URL looks good."
        controls.url_hint.update()
        suggestion = await controller.suggest_article_from_url(url=normalized)
        suggested_type = normalize_requested_share_type(str(suggestion.get("suggested_learning_item_type") or "article"))
        title = str(suggestion.get("title") or "").strip()
        raw_tags = suggestion.get("suggested_tags")
        iterable_tags = raw_tags if isinstance(raw_tags, list) else []
        tags = [str(tag).strip() for tag in iterable_tags if str(tag).strip()]
        state.latest_suggestions = {"title": title, "tags": ", ".join(tags[:8])}
        if title and not str(controls.title_input.value or "").strip():
            controls.title_input.value = title
        if state.latest_suggestions.get("tags") and not str(controls.tags_input.value or "").strip():
            controls.tags_input.value = str(state.latest_suggestions["tags"])
        refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type="article",
            source_url=normalized,
            suggested_type=suggested_type,
        )
        controls.suggestion_hint.text = f"Suggested: {title}" if title else ""
        controls.suggestion_hint.update()
        controls.preview.refresh()
        notify("Metadata imported", type="positive")

    @guard_ui_action(title="Publish failed")
    async def _publish() -> None:
        title = str(controls.title_input.value or "").strip()
        url = normalize_http_url(str(controls.url_input.value or ""))
        if not title:
            notify("Article title is required", type="negative")
            return
        if not url:
            notify("Valid learning item URL is required", type="negative")
            return
        payload: dict[str, object] = {
            "title": title,
            "url": url,
            "tags": str(controls.tags_input.value or "").strip(),
        }
        await controller.create_article(payload=payload)
        complete_share_publish(
            item_type="article",
            draft_key=draft_key,
            app_module=app_module,
            ui_module=ui_module,
            notify=notify,
        )

    controls.import_btn.on("click", lambda *_: _import_metadata())
    controls.publish_btn.on("click", lambda *_: _publish())
