"""Course and video action wiring for learning-item share routes."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.helpers import normalize_requested_share_type, validate_course_like_publish
from frontend.ui.nicegui.pages.share.page_item_drafts import refresh_detected_type_hint, refresh_title_suggestion
from frontend.ui.nicegui.pages.share.page_item_form import CourseShareControls, normalize_http_url
from frontend.ui.nicegui.pages.share.state import ShareCourseUiState


def wire_course_actions(
    *,
    controls: CourseShareControls,
    state: ShareCourseUiState,
    controller: SharePageController,
    draft_key: str,
    item_type: str,
    app_module: Any,
    ui_module: Any,
    notify: Any,
) -> None:
    """Bind import/apply/publish behavior for course/video share routes."""

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
        if normalize_requested_share_type(item_type) == "video":
            suggestion = await controller.suggest_video_from_url(url=normalized)
        else:
            suggestion = await controller.suggest_course_from_url(url=normalized)
        suggested_type = normalize_requested_share_type(str(suggestion.get("suggested_learning_item_type") or item_type))
        state.latest_suggestions = {
            "title": str(suggestion.get("title") or "").strip(),
            "description": str(suggestion.get("description") or "").strip(),
            "provider": str(suggestion.get("suggested_provider") or "").strip(),
            "category": str(suggestion.get("suggested_category") or "").strip(),
        }
        if state.latest_suggestions.get("title") and not str(controls.title_input.value or "").strip():
            controls.title_input.value = str(state.latest_suggestions["title"])
        if state.latest_suggestions.get("description") and not str(controls.description_input.value or "").strip():
            controls.description_input.value = str(state.latest_suggestions["description"])
        if state.latest_suggestions.get("provider") and not str(controls.provider_input.value or "").strip():
            controls.provider_input.value = str(state.latest_suggestions["provider"])
        if state.latest_suggestions.get("category") and not str(controls.category_input.value or "").strip():
            controls.category_input.value = str(state.latest_suggestions["category"])
        refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type=item_type,
            source_url=normalized,
            suggested_type=suggested_type,
        )
        refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()
        notify("Metadata imported", type="positive")

    def _apply_title_suggestion() -> None:
        suggested = str(state.latest_suggestions.get("title") or "").strip()
        if not suggested:
            notify("No title suggestion available", type="warning")
            return
        controls.title_input.value = suggested
        refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()

    @guard_ui_action(title="Publish failed")
    async def _publish() -> None:
        title = str(controls.title_input.value or "").strip()
        description = str(controls.description_input.value or "").strip()
        url = normalize_http_url(str(controls.url_input.value or ""))
        validation_error = validate_course_like_publish(
            item_type=item_type,
            title=title,
            description=description,
            url=url,
        )
        if validation_error:
            notify(validation_error, type="negative")
            return
        payload: dict[str, object] = {
            "title": title,
            "description": description,
            "provider": str(controls.provider_input.value or "").strip(),
            "category": str(controls.category_input.value or "").strip(),
            "url": url,
        }
        if normalize_requested_share_type(item_type) == "video" and not str(payload["provider"] or "").strip():
            payload["provider"] = "YouTube"
        if normalize_requested_share_type(item_type) == "video":
            await controller.create_video(payload=payload)
            app_module.storage.user.pop(draft_key, None)
            notify("Learning item published", type="positive")
            ui_module.navigate.to("/explore?tab=videos")
            return
        await controller.create_course(payload=payload)
        app_module.storage.user.pop(draft_key, None)
        notify("Learning item published", type="positive")
        ui_module.navigate.to("/explore?tab=courses")

    controls.import_btn.on("click", lambda *_: _import_metadata())
    controls.apply_title_btn.on("click", lambda *_: _apply_title_suggestion())
    controls.publish_btn.on("click", lambda *_: _publish())
