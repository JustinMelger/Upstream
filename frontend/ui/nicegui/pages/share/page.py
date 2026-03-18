"""Dedicated share page for learning-item publishing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import app, ui
from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.learning_items import learning_item_type_label
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait
from frontend.ui.nicegui.pages.share.controller import SharePageController
from frontend.ui.nicegui.pages.share.helpers import (
    normalize_requested_share_type,
    share_detected_type_text,
    share_route_for_type,
    share_subtitle_for_type,
    share_title_input_label,
    validate_course_like_publish,
)
from frontend.ui.nicegui.pages.share.state import ShareArticleUiState, ShareCourseUiState


_HTTP_URL_ADAPTER: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def _normalize_http_url(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        return str(_HTTP_URL_ADAPTER.validate_python(value))
    except ValidationError:
        return ""


@dataclass(slots=True)
class CourseShareControls:
    url_input: Any
    url_hint: Any
    type_hint: Any
    import_btn: Any
    title_input: Any
    title_suggestion: Any
    apply_title_btn: Any
    description_input: Any
    provider_input: Any
    category_input: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


@dataclass(slots=True)
class ArticleShareControls:
    url_input: Any
    url_hint: Any
    type_hint: Any
    import_btn: Any
    title_input: Any
    tags_input: Any
    suggestion_hint: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


@dataclass(slots=True)
class PathShareControls:
    name_input: Any
    description_input: Any
    course_ids_input: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


def _render_share_scaffold(*, title: str, subtitle: str) -> None:
    with ui.column().classes("w-full gap-1 lp-share-header"):
        ui.label(title).classes("lp-home-title")
        ui.label(subtitle).classes("text-sm").style("color: var(--lp-muted)")


def _render_share_type_picker(*, current_type: str) -> None:
    with ui.row().classes("w-full items-center gap-2 flex-wrap"):
        ui.label("Type").classes("text-xs").style("color: var(--lp-muted)")
        for item_type in ("video", "course", "article"):
            is_current = normalize_requested_share_type(current_type) == item_type
            btn = ui.button(
                learning_item_type_label(item_type),
                on_click=lambda _item_type=item_type: ui.navigate.to(share_route_for_type(_item_type)),
            ).props("dense" if is_current else "outline dense")
            if is_current:
                btn.classes("lp-explore-category-btn--active")


def _build_course_controls(*, item_type: str) -> CourseShareControls:
    item_label = learning_item_type_label(item_type)
    with ui.card().classes("lp-card w-full lp-share-surface"):
        with ui.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui.label("Import learning item").classes("lp-home-section-title")
                url_input = ui.input("https://...").props("clearable dense").classes("w-full lp-share-input")
                url_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
                type_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
                import_btn = ui.button("Import metadata").props("unelevated no-caps").classes("lp-share-import-btn")
                ui.separator()
                ui.label("Learning item details").classes("lp-home-section-title")
                title_input = (
                    ui.input(share_title_input_label(item_type)).props("clearable dense").classes("w-full lp-share-input")
                )
                with ui.row().classes("w-full items-center justify-between lp-share-suggestion-row"):
                    title_suggestion = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
                    apply_title_btn = ui.button("Apply suggestion").props("dense outline no-caps")
                description_input = (
                    ui.textarea("Description").props("autogrow dense maxlength=300").classes("w-full lp-share-input")
                )
                with ui.row().classes("w-full gap-2 lp-share-grid-two"):
                    provider_input = ui.input("Provider").props("clearable dense").classes("w-full lp-share-input")
                    category_input = ui.input("Category").props("clearable dense").classes("w-full lp-share-input")

            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui.label("Learning item preview").classes("lp-home-section-title")

                @ui.refreshable
                def preview() -> None:
                    with ui.card().classes("lp-card w-full lp-share-preview-card"):
                        ui.label(str(title_input.value or share_title_input_label(item_type))).classes("text-md font-semibold")
                        provider = str(provider_input.value or "").strip() or "Provider"
                        category = str(category_input.value or "").strip() or "Category"
                        ui.label(f"{provider} · {category}").classes("text-xs").style("color: var(--lp-muted)")
                        ui.separator()
                        ui.label(str(description_input.value or "Description preview")).classes("text-sm").style(
                            "color: var(--lp-muted)"
                        )
                        source_url = _normalize_http_url(str(url_input.value or ""))
                        if source_url:
                            ui.button(
                                "Open learning item", on_click=lambda u=source_url: ui.navigate.to(u, new_tab=True)
                            ).props("dense outline no-caps")

                preview()

        with ui.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui.button("Publish Learning Item").props("unelevated no-caps").classes("lp-share-publish-btn")

    return CourseShareControls(
        url_input=url_input,
        url_hint=url_hint,
        type_hint=type_hint,
        import_btn=import_btn,
        title_input=title_input,
        title_suggestion=title_suggestion,
        apply_title_btn=apply_title_btn,
        description_input=description_input,
        provider_input=provider_input,
        category_input=category_input,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )


def _build_article_controls() -> ArticleShareControls:
    with ui.card().classes("lp-card w-full lp-share-surface"):
        with ui.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui.label("Import learning item").classes("lp-home-section-title")
                url_input = ui.input("https://...").props("clearable dense").classes("w-full lp-share-input")
                url_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
                type_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
                import_btn = ui.button("Import metadata").props("unelevated no-caps").classes("lp-share-import-btn")
                ui.separator()
                ui.label("Learning item details").classes("lp-home-section-title")
                title_input = (
                    ui.input(share_title_input_label("article")).props("clearable dense").classes("w-full lp-share-input")
                )
                tags_input = ui.input("Tags (comma-separated)").props("clearable dense").classes("w-full lp-share-input")
                suggestion_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")

            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui.label("Learning item preview").classes("lp-home-section-title")

                @ui.refreshable
                def preview() -> None:
                    with ui.card().classes("lp-card w-full lp-share-preview-card"):
                        ui.label(str(title_input.value or "Article title")).classes("text-md font-semibold")
                        ui.label(str(tags_input.value or "No tags")).classes("text-xs").style("color: var(--lp-muted)")
                        source_url = _normalize_http_url(str(url_input.value or ""))
                        if source_url:
                            ui.button(
                                "Open learning item", on_click=lambda u=source_url: ui.navigate.to(u, new_tab=True)
                            ).props("dense outline no-caps")

                preview()

        with ui.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui.button("Publish Learning Item").props("unelevated no-caps").classes("lp-share-publish-btn")

    return ArticleShareControls(
        url_input=url_input,
        url_hint=url_hint,
        type_hint=type_hint,
        import_btn=import_btn,
        title_input=title_input,
        tags_input=tags_input,
        suggestion_hint=suggestion_hint,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )


def _build_path_controls(*, course_options: dict[int, str]) -> PathShareControls:
    with ui.card().classes("lp-card w-full lp-share-surface"):
        with ui.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui.label("Path details").classes("lp-home-section-title")
                name_input = ui.input("Path name").props("clearable dense").classes("w-full lp-share-input")
                description_input = (
                    ui.textarea("Description").props("autogrow dense maxlength=400").classes("w-full lp-share-input")
                )
                course_ids_input = (
                    ui.select(course_options, label="Courses in order", multiple=True)
                    .props("dense")
                    .classes("w-full lp-share-input")
                )

            with ui.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui.label("Path preview").classes("lp-home-section-title")

                @ui.refreshable
                def preview() -> None:
                    with ui.card().classes("lp-card w-full lp-share-preview-card"):
                        ui.label(str(name_input.value or "Path name")).classes("text-md font-semibold")
                        selected_ids = [
                            int(course_id) for course_id in list(course_ids_input.value or []) if int(course_id) > 0
                        ]
                        ui.label(f"{len(selected_ids)} courses selected").classes("text-xs").style("color: var(--lp-muted)")
                        ui.separator()
                        ui.label(str(description_input.value or "Path description preview")).classes("text-sm").style(
                            "color: var(--lp-muted)"
                        )

                preview()

        with ui.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui.button("Publish Path").props("unelevated no-caps").classes("lp-share-publish-btn")

    return PathShareControls(
        name_input=name_input,
        description_input=description_input,
        course_ids_input=course_ids_input,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )


def _wire_course_draft(*, controls: CourseShareControls, draft_key: str, item_type: str) -> None:
    def _save(*, notify: bool) -> None:
        app.storage.user[draft_key] = {
            "url": str(controls.url_input.value or ""),
            "title": str(controls.title_input.value or ""),
            "description": str(controls.description_input.value or ""),
            "provider": str(controls.provider_input.value or ""),
            "category": str(controls.category_input.value or ""),
        }
        if notify:
            safe_notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.url_input.value = str(raw.get("url") or "")
        controls.title_input.value = str(raw.get("title") or "")
        controls.description_input.value = str(raw.get("description") or "")
        controls.provider_input.value = str(raw.get("provider") or "")
        controls.category_input.value = str(raw.get("category") or "")

    controls.save_btn.on("click", lambda *_: _save(notify=True))

    def _on_field_change(*_args: Any) -> None:
        _save(notify=False)
        _refresh_detected_type_hint(
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
    _refresh_detected_type_hint(
        hint_control=controls.type_hint,
        current_type=item_type,
        source_url=str(controls.url_input.value or ""),
    )


def _wire_article_draft(*, controls: ArticleShareControls, draft_key: str) -> None:
    def _save(*, notify: bool) -> None:
        app.storage.user[draft_key] = {
            "url": str(controls.url_input.value or ""),
            "title": str(controls.title_input.value or ""),
            "tags": str(controls.tags_input.value or ""),
        }
        if notify:
            safe_notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.url_input.value = str(raw.get("url") or "")
        controls.title_input.value = str(raw.get("title") or "")
        controls.tags_input.value = str(raw.get("tags") or "")

    controls.save_btn.on("click", lambda *_: _save(notify=True))

    def _on_field_change(*_args: Any) -> None:
        _save(notify=False)
        _refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type="article",
            source_url=str(controls.url_input.value or ""),
        )
        controls.preview.refresh()

    for control in [controls.url_input, controls.title_input, controls.tags_input]:
        control.on("update:model-value", _on_field_change)

    _load()
    _refresh_detected_type_hint(
        hint_control=controls.type_hint,
        current_type="article",
        source_url=str(controls.url_input.value or ""),
    )


def _wire_path_draft(*, controls: PathShareControls, draft_key: str) -> None:
    def _save(*, notify: bool) -> None:
        app.storage.user[draft_key] = {
            "name": str(controls.name_input.value or ""),
            "description": str(controls.description_input.value or ""),
            "course_ids": list(controls.course_ids_input.value or []),
        }
        if notify:
            safe_notify("Draft saved", type="positive")

    def _load() -> None:
        raw = app.storage.user.get(draft_key)
        if not isinstance(raw, dict):
            return
        controls.name_input.value = str(raw.get("name") or "")
        controls.description_input.value = str(raw.get("description") or "")
        controls.course_ids_input.value = list(raw.get("course_ids") or [])
        controls.course_ids_input.update()

    controls.save_btn.on("click", lambda *_: _save(notify=True))

    def _on_field_change(*_args: Any) -> None:
        _save(notify=False)
        controls.preview.refresh()

    for control in [controls.name_input, controls.description_input, controls.course_ids_input]:
        control.on("update:model-value", _on_field_change)

    _load()


def _refresh_title_suggestion(*, controls: CourseShareControls, state: ShareCourseUiState) -> None:
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


def _refresh_detected_type_hint(*, hint_control: Any, current_type: str, source_url: str, suggested_type: str = "") -> None:
    hint_control.text = share_detected_type_text(
        current_type=current_type,
        source_url=source_url,
        suggested_type=suggested_type,
    )
    hint_control.update()


def _wire_course_actions(
    *,
    controls: CourseShareControls,
    state: ShareCourseUiState,
    controller: SharePageController,
    draft_key: str,
    item_type: str,
) -> None:
    @guard_ui_action(title="Import failed")
    async def _import_metadata() -> None:
        raw_url = str(controls.url_input.value or "").strip()
        normalized = _normalize_http_url(raw_url)
        if not normalized:
            controls.url_hint.text = "Enter a valid http(s) URL."
            controls.url_hint.update()
            safe_notify("Enter a valid URL first", type="negative")
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
        _refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type=item_type,
            source_url=normalized,
            suggested_type=suggested_type,
        )
        _refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()
        safe_notify("Metadata imported", type="positive")

    def _apply_title_suggestion() -> None:
        suggested = str(state.latest_suggestions.get("title") or "").strip()
        if not suggested:
            safe_notify("No title suggestion available", type="warning")
            return
        controls.title_input.value = suggested
        _refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()

    @guard_ui_action(title="Publish failed")
    async def _publish() -> None:
        title = str(controls.title_input.value or "").strip()
        description = str(controls.description_input.value or "").strip()
        url = _normalize_http_url(str(controls.url_input.value or ""))
        validation_error = validate_course_like_publish(
            item_type=item_type,
            title=title,
            description=description,
            url=url,
        )
        if validation_error:
            safe_notify(validation_error, type="negative")
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
            created = await controller.create_video(payload=payload)
            created_raw_id = created.get("id")
            created_id = created_raw_id if isinstance(created_raw_id, int) else 0
            app.storage.user.pop(draft_key, None)
            safe_notify("Learning item published", type="positive")
            ui.navigate.to(f"/explore/videos/{created_id}" if created_id > 0 else "/explore")
            return
        await controller.create_course(payload=payload)
        app.storage.user.pop(draft_key, None)
        safe_notify("Learning item published", type="positive")
        ui.navigate.to("/explore?tab=courses")

    controls.import_btn.on("click", lambda *_: _import_metadata())
    controls.apply_title_btn.on("click", lambda *_: _apply_title_suggestion())
    controls.publish_btn.on("click", lambda *_: _publish())


def _wire_article_actions(
    *,
    controls: ArticleShareControls,
    state: ShareArticleUiState,
    controller: SharePageController,
    draft_key: str,
) -> None:
    @guard_ui_action(title="Import failed")
    async def _import_metadata() -> None:
        raw_url = str(controls.url_input.value or "").strip()
        normalized = _normalize_http_url(raw_url)
        if not normalized:
            controls.url_hint.text = "Enter a valid http(s) URL."
            controls.url_hint.update()
            safe_notify("Enter a valid URL first", type="negative")
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
        _refresh_detected_type_hint(
            hint_control=controls.type_hint,
            current_type="article",
            source_url=normalized,
            suggested_type=suggested_type,
        )
        controls.suggestion_hint.text = f"Suggested: {title}" if title else ""
        controls.suggestion_hint.update()
        controls.preview.refresh()
        safe_notify("Metadata imported", type="positive")

    @guard_ui_action(title="Publish failed")
    async def _publish() -> None:
        title = str(controls.title_input.value or "").strip()
        url = _normalize_http_url(str(controls.url_input.value or ""))
        if not title:
            safe_notify("Article title is required", type="negative")
            return
        if not url:
            safe_notify("Valid learning item URL is required", type="negative")
            return
        payload: dict[str, object] = {
            "title": title,
            "url": url,
            "tags": str(controls.tags_input.value or "").strip(),
        }
        await controller.create_article(payload=payload)
        app.storage.user.pop(draft_key, None)
        safe_notify("Learning item published", type="positive")
        ui.navigate.to("/explore?tab=articles")

    controls.import_btn.on("click", lambda *_: _import_metadata())
    controls.publish_btn.on("click", lambda *_: _publish())


async def _render_share_course_page(
    *,
    store: SessionStore,
    api: ApiClient,
    controller: SharePageController,
    item_type: str,
) -> None:
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    normalized_type = normalize_requested_share_type(item_type)
    draft_key = f"share_{normalized_type}_page_draft::{username}"
    state = ShareCourseUiState()

    render_shell(title="Share Learning Item", store=store, api=api)
    with render_catalog_scope(variant="explore").classes("lp-container lp-share-scope"):
        _render_share_type_picker(current_type=normalized_type)
        _render_share_scaffold(
            title="Share Learning Item",
            subtitle=share_subtitle_for_type(normalized_type),
        )
        controls = _build_course_controls(item_type=normalized_type)
        _wire_course_draft(controls=controls, draft_key=draft_key, item_type=normalized_type)
        _wire_course_actions(
            controls=controls,
            state=state,
            controller=controller,
            draft_key=draft_key,
            item_type=normalized_type,
        )
        _refresh_title_suggestion(controls=controls, state=state)
        controls.preview.refresh()


async def _render_share_article_page(*, store: SessionStore, api: ApiClient, controller: SharePageController) -> None:
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    draft_key = f"share_article_page_draft::{username}"
    state = ShareArticleUiState()

    render_shell(title="Share Learning Item", store=store, api=api)
    with render_catalog_scope(variant="explore").classes("lp-container lp-share-scope"):
        _render_share_type_picker(current_type="article")
        _render_share_scaffold(
            title="Share Learning Item",
            subtitle=share_subtitle_for_type("article"),
        )
        controls = _build_article_controls()
        _wire_article_draft(controls=controls, draft_key=draft_key)
        _wire_article_actions(controls=controls, state=state, controller=controller, draft_key=draft_key)
        controls.preview.refresh()


async def _render_share_path_page(*, store: SessionStore, api: ApiClient, controller: SharePageController) -> None:
    user = await require_user(store, api)
    if user is None:
        return
    username = str(user.get("username") or "")
    draft_key = f"share_path_page_draft::{username}"
    course_options = await controller.load_path_course_options()

    render_shell(title="Share Path", store=store, api=api)
    with render_catalog_scope(variant="explore").classes("lp-container lp-share-scope"):
        _render_share_scaffold(
            title="Share Path",
            subtitle="Share a structured path your team can follow together.",
        )
        controls = _build_path_controls(course_options=course_options)
        _wire_path_draft(controls=controls, draft_key=draft_key)

        @guard_ui_action(title="Publish failed")
        async def _publish() -> None:
            name = str(controls.name_input.value or "").strip()
            description = str(controls.description_input.value or "").strip()
            course_ids: list[int] = []
            for raw in list(controls.course_ids_input.value or []):
                try:
                    course_id = int(raw)
                except (TypeError, ValueError):
                    continue
                if course_id > 0:
                    course_ids.append(course_id)
            if not name:
                safe_notify("Path name is required", type="negative")
                return
            if not course_ids:
                safe_notify("Select at least one course", type="negative")
                return
            created = await controller.create_path(
                payload={
                    "name": name,
                    "description": description,
                    "course_ids": course_ids,
                }
            )
            app.storage.user.pop(draft_key, None)
            safe_notify("Path published", type="positive")
            created_raw_id = created.get("id")
            created_id = created_raw_id if isinstance(created_raw_id, int) else 0
            ui.navigate.to(f"/explore/paths/{created_id}" if created_id > 0 else "/explore?tab=paths")

        controls.publish_btn.on("click", lambda *_: _publish())
        controls.preview.refresh()


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register dedicated learning-item share routes."""
    controller = SharePageController(api=api)

    @ui.page("/share/item")
    async def share_item_page() -> None:
        request = getattr(ui.context.client, "request", None)
        query_params = getattr(request, "query_params", None)
        item_type = normalize_requested_share_type(str((query_params or {}).get("type", "course")))
        if item_type == "article":
            await _render_share_article_page(store=store, api=api, controller=controller)
            return
        await _render_share_course_page(store=store, api=api, controller=controller, item_type=item_type)

    @ui.page("/share/path")
    async def share_path_page() -> None:
        await _render_share_path_page(store=store, api=api, controller=controller)

    @ui.page("/share/course")
    async def share_course_compat_page() -> None:
        track_ui_event_nowait(
            api=api,
            event_name="share_compat_redirect_used",
            context={"from": "/share/course", "to": "/share/item", "item_type": "course"},
        )
        ui.navigate.to("/share/item?type=course")

    @ui.page("/share/article")
    async def share_article_compat_page() -> None:
        track_ui_event_nowait(
            api=api,
            event_name="share_compat_redirect_used",
            context={"from": "/share/article", "to": "/share/item", "item_type": "article"},
        )
        ui.navigate.to("/share/item?type=article")
