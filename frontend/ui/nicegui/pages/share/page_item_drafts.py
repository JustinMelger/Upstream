"""Draft persistence helpers for learning-item share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.share.helpers import share_detected_type_text
from frontend.ui.nicegui.pages.share.page_item_form import ArticleShareControls, CourseShareControls
from frontend.ui.nicegui.pages.share.state import ShareCourseUiState


def refresh_title_suggestion(*, controls: CourseShareControls, state: ShareCourseUiState) -> None:
    """Refresh the visible title suggestion hint."""
    suggested = str(state.latest_suggestions.get("title") or "").strip()
    current = str(controls.title_input.value or "").strip()
    if suggested and suggested != current:
        controls.title_suggestion.text = f"Suggested: {suggested}"
        controls.apply_title_btn.visible = True
    else:
        controls.title_suggestion.text = ""
        controls.apply_title_btn.visible = False
    controls.title_suggestion.update()
    controls.apply_title_btn.update()


def refresh_detected_type_hint(*, hint_control: Any, current_type: str, source_url: str, suggested_type: str = "") -> None:
    """Refresh the inferred-type hint from URL/metadata."""
    hint_control.text = share_detected_type_text(
        current_type=current_type,
        source_url=source_url,
        suggested_type=suggested_type,
    )
    hint_control.update()


def wire_course_draft(*, controls: CourseShareControls, draft_key: str, item_type: str, app_module: Any, notify: Any) -> None:
    """Bind autosave/recovery behavior for course/video drafts."""

    def _save(*, show_notice: bool) -> None:
        app_module.storage.user[draft_key] = {
            "url": str(controls.url_input.value or ""),
            "title": str(controls.title_input.value or ""),
            "description": str(controls.description_input.value or ""),
            "provider": str(controls.provider_input.value or ""),
            "category": str(controls.category_input.value or ""),
        }
        if show_notice:
            notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app_module.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.url_input.value = str(raw.get("url") or "")
        controls.title_input.value = str(raw.get("title") or "")
        controls.description_input.value = str(raw.get("description") or "")
        controls.provider_input.value = str(raw.get("provider") or "")
        controls.category_input.value = str(raw.get("category") or "")

    controls.save_btn.on("click", lambda *_: _save(show_notice=True))

    def _on_field_change(*_args: Any) -> None:
        _save(show_notice=False)
        refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type=item_type,
            source_url=str(controls.url_input.value or ""),
        )
        controls.preview.refresh()

    for control in [
        controls.url_input,
        controls.title_input,
        controls.description_input,
        controls.provider_input,
        controls.category_input,
    ]:
        control.on("update:model-value", _on_field_change)

    _load()
    refresh_detected_type_hint(
        hint_control=controls.type_hint,
        current_type=item_type,
        source_url=str(controls.url_input.value or ""),
    )


def wire_article_draft(*, controls: ArticleShareControls, draft_key: str, app_module: Any, notify: Any) -> None:
    """Bind autosave/recovery behavior for article drafts."""

    def _save(*, show_notice: bool) -> None:
        app_module.storage.user[draft_key] = {
            "url": str(controls.url_input.value or ""),
            "title": str(controls.title_input.value or ""),
            "tags": str(controls.tags_input.value or ""),
        }
        if show_notice:
            notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app_module.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.url_input.value = str(raw.get("url") or "")
        controls.title_input.value = str(raw.get("title") or "")
        controls.tags_input.value = str(raw.get("tags") or "")

    controls.save_btn.on("click", lambda *_: _save(show_notice=True))

    def _on_field_change(*_args: Any) -> None:
        _save(show_notice=False)
        refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type="article",
            source_url=str(controls.url_input.value or ""),
        )
        controls.preview.refresh()

    for control in [controls.url_input, controls.title_input, controls.tags_input]:
        control.on("update:model-value", _on_field_change)

    _load()
    refresh_detected_type_hint(
        hint_control=controls.type_hint,
        current_type="article",
        source_url=str(controls.url_input.value or ""),
    )
