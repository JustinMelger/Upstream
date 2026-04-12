"""Dialog builders for the Courses page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui
from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.clipboard import copy_text_to_clipboard
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.metadata_fallback import build_course_metadata_fallback
from frontend.ui.nicegui.core.suggestion_utils import suggestion_badge_text


_HTTP_URL_ADAPTER: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def _normalize_http_url(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        return str(_HTTP_URL_ADAPTER.validate_python(value))
    except ValidationError:
        return ""


def _cache_suggestion(*, suggestions: dict[str, str], key: str, value: str) -> None:
    cleaned = str(value or "").strip()
    if cleaned:
        suggestions[key] = cleaned
    else:
        suggestions.pop(key, None)


def _apply_course_suggestion(
    *,
    key: str,
    latest_suggestions: dict[str, str],
    controls: dict[str, Any],
    suggested_values: dict[str, str],
    only_if_empty: bool,
) -> bool:
    value = str(latest_suggestions.get(key) or "").strip()
    if not value:
        return False
    control = controls.get(key)
    if control is None:
        return False
    if only_if_empty and str(control.value or "").strip():
        return False
    control.value = value
    if key in {"title", "description", "provider", "category"}:
        suggested_values[key] = value
    return True


def build_share_course_dialog(  # noqa: C901, PLR0915
    *,
    username: str,
    parse_duration_hours: Callable[[str], float | None],
    on_submit: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    on_suggest_from_url: Callable[[str], Awaitable[dict[str, Any]]],
    is_duplicate_url: Callable[[str], bool] | None = None,
) -> Callable[[], None]:
    """Build share-course dialog and return an open helper."""
    create_dialog = ui.dialog()
    with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
        ui.label("Share Learning Item").classes("text-xl font-semibold")
        ui.label("Save a draft if you want feedback before publishing.").classes("text-xs").style("color: var(--lp-muted)")

        create_title = ui.input("Title").props("clearable").classes("w-full")
        create_description = ui.textarea("Description").props("autogrow").classes("w-full")
        create_provider = ui.input("Provider").props("clearable").classes("w-full")
        create_category = ui.input("Category").props("clearable").classes("w-full")
        create_url = ui.input("URL").props("clearable").classes("w-full")
        title_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        description_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        provider_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        category_suggest_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        url_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")
        auto_suggest_state: dict[str, int | str] = {"nonce": 0, "last_source": ""}
        auto_draft_state: dict[str, int | bool] = {"nonce": 0, "enabled": True}
        suggested_values: dict[str, str] = {}
        latest_suggestions: dict[str, str] = {}
        fallback_examples: dict[str, str] = {}
        course_draft_key = f"courses_share_draft::{username}"

        def _course_draft_payload() -> dict[str, Any]:
            return {
                "title": str(create_title.value or ""),
                "description": str(create_description.value or "").strip(),
                "provider": str(create_provider.value or ""),
                "category": str(create_category.value or ""),
                "language": str(create_language.value or ""),
                "level": str(create_level.value or ""),
                "learning_outcomes": str(create_learning_outcomes.value or "").strip(),
                "prerequisites": str(create_prerequisites.value or "").strip(),
                "duration_hours": str(create_duration_hours.value or ""),
                "url": str(create_url.value or ""),
            }

        def _draft_has_content(raw: Any) -> bool:
            if not isinstance(raw, dict):
                return False
            return any(str(v or "").strip() for v in raw.values())

        def _save_draft_silent() -> None:
            if not bool(auto_draft_state.get("enabled", True)):
                return
            app.storage.user[course_draft_key] = _course_draft_payload()

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

        def _refresh_suggestion_hints() -> None:
            title_suggest_hint.text = suggestion_badge_text(
                current_value=str(create_title.value or ""),
                suggested_value=str(suggested_values.get("title") or ""),
            )
            description_suggest_hint.text = suggestion_badge_text(
                current_value=str(create_description.value or ""),
                suggested_value=str(suggested_values.get("description") or ""),
            )
            provider_suggest_hint.text = suggestion_badge_text(
                current_value=str(create_provider.value or ""),
                suggested_value=str(suggested_values.get("provider") or ""),
            )
            category_suggest_hint.text = suggestion_badge_text(
                current_value=str(create_category.value or ""),
                suggested_value=str(suggested_values.get("category") or ""),
            )

        fallback_hint = ui.label("").classes("text-xs").style("color: var(--lp-muted)")

        def _refresh_fallback_hint() -> None:
            if not fallback_examples:
                fallback_hint.text = ""
                return
            fallback_hint.text = (
                "Metadata unavailable. Example values ready: "
                f"title='{fallback_examples.get('title', '')}', "
                f"provider='{fallback_examples.get('provider', '')}', "
                f"category='{fallback_examples.get('category', '')}'."
            )

        with ui.row().classes("items-center justify-between w-full -mt-2"):
            ui.label("Paste a link and auto-suggest metadata.").classes("text-xs").style("color: var(--lp-muted)")

            def _refresh_url_hint() -> bool:
                normalized = _normalize_http_url(str(create_url.value or ""))
                if not str(create_url.value or "").strip():
                    url_hint.text = ""
                    return True
                if not normalized:
                    url_hint.text = "Enter a valid http(s) URL."
                    return False
                if is_duplicate_url is not None and is_duplicate_url(normalized):
                    url_hint.text = "Similar URL already exists in the catalog."
                    return True
                url_hint.text = "URL looks good."
                return True

            async def _suggest_from_url(*, auto_trigger: bool = False) -> None:
                source_url = str(create_url.value or "").strip()
                if not source_url:
                    if not auto_trigger:
                        safe_notify("Enter a URL first", type="warning")
                    return
                if auto_trigger and source_url == str(auto_suggest_state.get("last_source") or ""):
                    return
                payload = await on_suggest_from_url(source_url)
                normalized_url = str(payload.get("normalized_url") or "").strip()
                suggested_title = str(payload.get("title") or "").strip()
                suggested_description = str(payload.get("description") or "").strip()
                suggested_provider = str(payload.get("suggested_provider") or "").strip()
                suggested_category = str(payload.get("suggested_category") or "").strip()
                suggested_tags = [str(tag).strip() for tag in list(payload.get("suggested_tags") or []) if str(tag).strip()]
                suggested_outcomes = "Suggested topics: " + ", ".join(suggested_tags[:6]) if suggested_tags else ""

                _cache_suggestion(suggestions=latest_suggestions, key="title", value=suggested_title)
                _cache_suggestion(suggestions=latest_suggestions, key="description", value=suggested_description)
                _cache_suggestion(suggestions=latest_suggestions, key="provider", value=suggested_provider)
                _cache_suggestion(suggestions=latest_suggestions, key="category", value=suggested_category)
                _cache_suggestion(suggestions=latest_suggestions, key="learning_outcomes", value=suggested_outcomes)
                has_suggestions = any(
                    [suggested_title, suggested_description, suggested_provider, suggested_category, suggested_tags]
                )
                fallback_examples.clear()
                if not has_suggestions:
                    fallback_examples.update(build_course_metadata_fallback(url=normalized_url or source_url))
                _refresh_fallback_hint()

                if normalized_url:
                    create_url.value = normalized_url
                _apply_course_suggestion(
                    key="title",
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=True,
                )
                _apply_course_suggestion(
                    key="description",
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=True,
                )
                _apply_course_suggestion(
                    key="provider",
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=True,
                )
                _apply_course_suggestion(
                    key="category",
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=True,
                )
                _apply_course_suggestion(
                    key="learning_outcomes",
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=True,
                )

                auto_suggest_state["last_source"] = normalized_url or source_url
                if has_suggestions:
                    safe_notify("Suggestions applied", type="positive")
                else:
                    safe_notify("No suggestions found for this URL", type="warning")
                _refresh_url_hint()
                _refresh_suggestion_hints()

            def _apply_fallback_examples() -> None:
                if not fallback_examples:
                    safe_notify("No fallback examples available", type="warning")
                    return
                changed = False
                for key in ["title", "description", "provider", "category", "learning_outcomes"]:
                    value = str(fallback_examples.get(key) or "").strip()
                    if not value:
                        continue
                    if key == "title" and not str(create_title.value or "").strip():
                        create_title.value = value
                        changed = True
                    if key == "description" and not str(create_description.value or "").strip():
                        create_description.value = value
                        changed = True
                    if key == "provider" and not str(create_provider.value or "").strip():
                        create_provider.value = value
                        changed = True
                    if key == "category" and not str(create_category.value or "").strip():
                        create_category.value = value
                        changed = True
                    if key == "learning_outcomes" and not str(create_learning_outcomes.value or "").strip():
                        create_learning_outcomes.value = value
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
                changed = False
                for key in ["title", "description", "provider", "category", "learning_outcomes"]:
                    changed = (
                        _apply_course_suggestion(
                            key=key,
                            latest_suggestions=latest_suggestions,
                            controls=suggestion_controls,
                            suggested_values=suggested_values,
                            only_if_empty=False,
                        )
                        or changed
                    )
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
                changed = _apply_course_suggestion(
                    key=field_key,
                    latest_suggestions=latest_suggestions,
                    controls=suggestion_controls,
                    suggested_values=suggested_values,
                    only_if_empty=False,
                )
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

            create_url.on("blur", _queue_auto_suggest)
            create_url.on("paste", _queue_auto_suggest)
            create_url.on("update:model-value", lambda *_: _refresh_url_hint())
            create_title.on("update:model-value", lambda *_: _refresh_suggestion_hints())
            create_description.on("update:model-value", lambda *_: _refresh_suggestion_hints())
            create_provider.on("update:model-value", lambda *_: _refresh_suggestion_hints())
            create_category.on("update:model-value", lambda *_: _refresh_suggestion_hints())

            with ui.row().classes("items-center gap-2"):
                ui.button("Suggest from URL", on_click=_suggest_from_url_manual).props("outline dense")
                ui.button("Apply all suggestions", on_click=_apply_all_suggestions).props("outline dense")
                ui.button("Use fallback examples", on_click=_apply_fallback_examples).props("outline dense")
            with ui.row().classes("items-center gap-2"):
                ui.button("Re-suggest title", on_click=lambda: _resuggest_field("title", "Title")).props("flat dense")
                ui.button("Re-suggest description", on_click=lambda: _resuggest_field("description", "Description")).props(
                    "flat dense"
                )
                ui.button("Re-suggest provider", on_click=lambda: _resuggest_field("provider", "Provider")).props("flat dense")
                ui.button("Re-suggest category", on_click=lambda: _resuggest_field("category", "Category")).props("flat dense")
            _refresh_fallback_hint()
        create_language = ui.input("Language").props("clearable").classes("w-full")

        with ui.expansion("More fields").props("dense"):
            with ui.column().classes("w-full gap-3"):
                create_level = ui.input("Level").props("clearable").classes("w-full")
                create_learning_outcomes = ui.textarea("Learning outcomes (optional)").props("autogrow").classes("w-full")
                create_prerequisites = ui.textarea("Prerequisites (optional)").props("autogrow").classes("w-full")
                create_duration_hours = ui.input("Duration hours").props("clearable").classes("w-full")
        suggestion_controls: dict[str, Any] = {
            "title": create_title,
            "description": create_description,
            "provider": create_provider,
            "category": create_category,
            "learning_outcomes": create_learning_outcomes,
        }

        def _apply_course_draft(raw: Any) -> None:
            draft = raw if isinstance(raw, dict) else {}
            auto_draft_state["enabled"] = False
            create_title.value = str(draft.get("title") or "")
            create_description.value = str(draft.get("description") or "")
            create_provider.value = str(draft.get("provider") or "")
            create_category.value = str(draft.get("category") or "")
            create_language.value = str(draft.get("language") or "")
            create_level.value = str(draft.get("level") or "")
            create_learning_outcomes.value = str(draft.get("learning_outcomes") or "")
            create_prerequisites.value = str(draft.get("prerequisites") or "")
            create_duration_hours.value = str(draft.get("duration_hours") or "")
            create_url.value = str(draft.get("url") or "")
            suggested_values.clear()
            latest_suggestions.clear()
            fallback_examples.clear()
            _refresh_suggestion_hints()
            _refresh_fallback_hint()
            auto_draft_state["enabled"] = True

        def _discard_draft(*, reset_form: bool, notify: bool) -> None:
            app.storage.user.pop(course_draft_key, None)
            if reset_form:
                _apply_course_draft({})
                _refresh_url_hint()
            if notify:
                safe_notify("Draft discarded", type="positive")

        def _open_success_summary(*, created_row: dict[str, Any], autofilled_fields: list[str]) -> None:
            title = str(created_row.get("title") or "Course")
            source_url = str(created_row.get("url") or "").strip()
            course_id = int(created_row.get("id") or 0)

            def _share_another(summary_dialog: Any) -> None:
                summary_dialog.close()
                _apply_course_draft({})
                create_dialog.open()

            with ui.dialog() as summary_dialog, ui.card().classes("lp-card lp-dialog w-[min(640px,95vw)]"):
                ui.label("Course shared").classes("text-lg font-semibold")
                ui.label(f"{title} is now in the catalog.").classes("text-sm").style("color: var(--lp-muted)")
                if autofilled_fields:
                    ui.label("Autofilled fields: " + ", ".join(autofilled_fields)).classes("text-xs").style(
                        "color: var(--lp-muted)"
                    )
                with ui.row().classes("justify-end mt-4 gap-2"):
                    if course_id > 0:
                        ui.button(
                            "Open details",
                            on_click=lambda cid=course_id: ui.navigate.to(f"/explore/courses/{int(cid)}"),
                        ).props("outline")
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

            @guard_ui_action(title="Share learning item failed")
            async def _create_submit() -> None:
                dh_raw = str(create_duration_hours.value or "")
                dh = parse_duration_hours(dh_raw)
                if dh_raw.strip() and dh is None:
                    safe_notify("Duration hours must be a number", type="negative")
                    return
                if not _refresh_url_hint():
                    safe_notify("Enter a valid URL before sharing", type="negative")
                    return
                if not str(create_description.value or "").strip():
                    safe_notify("Description is required", type="negative")
                    return

                payload = {
                    "title": str(create_title.value or ""),
                    "description": str(create_description.value or "").strip(),
                    "provider": str(create_provider.value or ""),
                    "category": str(create_category.value or ""),
                    "language": str(create_language.value or ""),
                    "level": str(create_level.value or ""),
                    "learning_outcomes": str(create_learning_outcomes.value or "").strip(),
                    "prerequisites": str(create_prerequisites.value or "").strip(),
                    "duration_hours": dh,
                    "url": str(create_url.value or ""),
                }
                created_row = dict(await on_submit(payload) or {})
                _discard_draft(reset_form=False, notify=False)
                create_dialog.close()
                autofilled_fields: list[str] = []
                field_labels = {
                    "title": "Title",
                    "description": "Description",
                    "provider": "Provider",
                    "category": "Category",
                }
                for key, label in field_labels.items():
                    if (
                        suggestion_badge_text(
                            current_value=str(payload.get(key) or ""),
                            suggested_value=str(suggested_values.get(key) or ""),
                        )
                        == "Suggested"
                    ):
                        autofilled_fields.append(label)
                _open_success_summary(created_row=created_row, autofilled_fields=autofilled_fields)

            ui.button("Discard draft", on_click=lambda: _discard_draft(reset_form=True, notify=True)).props("outline")
            ui.button("Share", on_click=_create_submit)
            ui.button("Cancel", on_click=create_dialog.close).props("outline")

        for control in [
            create_title,
            create_description,
            create_provider,
            create_category,
            create_url,
            create_language,
            create_level,
            create_learning_outcomes,
            create_prerequisites,
            create_duration_hours,
        ]:
            control.on("update:model-value", _queue_draft_autosave)

    def _open_create_dialog() -> None:
        draft = app.storage.user.get(course_draft_key)
        _apply_course_draft(draft)
        _refresh_url_hint()
        _refresh_suggestion_hints()
        _refresh_fallback_hint()
        if _draft_has_content(draft):
            safe_notify("Recovered unsent draft", type="positive")
        create_dialog.open()

    return _open_create_dialog


def open_edit_course_dialog(
    *,
    course: dict[str, Any],
    parse_duration_hours: Callable[[str], float | None],
    on_save: Callable[[int, dict[str, Any]], Awaitable[None]],
) -> None:
    """Open edit-course dialog."""
    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
        ui.label("Edit Course").classes("text-xl font-semibold")

        course_id = int(course.get("id") or 0)
        title = ui.input("Title", value=str(course.get("title") or "")).props("clearable").classes("w-full")
        description = ui.textarea("Description", value=str(course.get("description") or "")).props("autogrow").classes("w-full")
        provider_new = ui.input("Provider", value=str(course.get("provider") or "")).props("clearable").classes("w-full")
        category_new = ui.input("Category", value=str(course.get("category") or "")).props("clearable").classes("w-full")
        language_new = ui.input("Language", value=str(course.get("language") or "")).props("clearable").classes("w-full")
        url = ui.input("URL", value=str(course.get("url") or "")).props("clearable").classes("w-full")

        with ui.expansion("More fields").props("dense"):
            with ui.column().classes("w-full gap-3"):
                level_new = ui.input("Level", value=str(course.get("level") or "")).props("clearable").classes("w-full")
                learning_outcomes_new = (
                    ui.textarea("Learning outcomes (optional)", value=str(course.get("learning_outcomes") or ""))
                    .props("autogrow")
                    .classes("w-full")
                )
                prerequisites_new = (
                    ui.textarea("Prerequisites (optional)", value=str(course.get("prerequisites") or ""))
                    .props("autogrow")
                    .classes("w-full")
                )
                duration_hours = (
                    ui.input("Duration hours", value=str(course.get("duration_hours") or ""))
                    .props("clearable")
                    .classes("w-full")
                )

        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Save changes failed")
            async def _save() -> None:
                dh_raw = str(duration_hours.value or "")
                dh = parse_duration_hours(dh_raw)
                if dh_raw.strip() and dh is None:
                    safe_notify("Duration hours must be a number", type="negative")
                    return
                if not str(description.value or "").strip():
                    safe_notify("Description is required", type="negative")
                    return

                payload = {
                    "title": str(title.value or ""),
                    "description": str(description.value or "").strip(),
                    "provider": str(provider_new.value or ""),
                    "category": str(category_new.value or ""),
                    "language": str(language_new.value or ""),
                    "level": str(level_new.value or ""),
                    "learning_outcomes": str(learning_outcomes_new.value or "").strip(),
                    "prerequisites": str(prerequisites_new.value or "").strip(),
                    "duration_hours": dh,
                    "url": str(url.value or ""),
                }
                await on_save(int(course_id), payload)
                safe_notify("Course updated", type="positive")
                dialog.close()

            ui.button("Save", on_click=_save)
            ui.button("Cancel", on_click=dialog.close).props("outline")

    dialog.open()


async def open_delete_course_dialog(
    *,
    course_id: int,
    on_delete: Callable[[int], Awaitable[None]],
) -> None:
    """Open delete confirmation dialog for a course."""
    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog"):
        ui.label("Delete this course?").classes("text-lg font-semibold")
        ui.label("This cannot be undone.").classes("text-sm text-gray-600")
        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Delete course failed")
            async def _delete() -> None:
                await on_delete(int(course_id))
                safe_notify("Course deleted", type="positive")
                dialog.close()

            ui.button("Delete", on_click=_delete).props("color=negative")
            ui.button("Cancel", on_click=dialog.close).props("outline")
    dialog.open()
