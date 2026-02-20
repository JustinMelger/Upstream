"""Dialog builders for the Courses page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify


async def open_recommend_course_dialog(
    *,
    course_id: int,
    username: str,
    load_recommendations: Callable[[int], Awaitable[list[dict[str, Any]]]],
    save_recommendation: Callable[[int, str], Awaitable[dict[str, Any]]],
    on_saved: Callable[[], Awaitable[None]],
) -> None:
    """Open recommend dialog for a course and persist note."""
    existing_note = ""
    try:
        rows = await load_recommendations(int(course_id))
        for row in list(rows or []):
            if not isinstance(row, dict):
                continue
            if str(row.get("created_by") or "") == username:
                existing_note = str(row.get("note") or "")
                break
    except ApiError:
        existing_note = ""

    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(600px,95vw)]"):
        ui.label("Recommend course").classes("text-lg font-semibold")
        note = ui.textarea("Why this helps (optional)", value=existing_note).props("autogrow").classes("w-full")
        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Recommend failed")
            async def _save() -> None:
                await save_recommendation(int(course_id), str(note.value or "").strip())
                safe_notify("Recommendation saved", type="positive")
                dialog.close()
                await on_saved()

            ui.button("Save", on_click=_save)
            ui.button("Cancel", on_click=dialog.close).props("outline")

    dialog.open()


def build_share_course_dialog(
    *,
    username: str,
    parse_duration_hours: Callable[[str], float | None],
    on_submit: Callable[[dict[str, Any]], Awaitable[None]],
) -> Callable[[], None]:
    """Build share-course dialog and return an open helper."""
    create_dialog = ui.dialog()
    with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
        ui.label("Share Course").classes("text-xl font-semibold")
        ui.label("Save a draft if you want feedback before publishing.").classes("text-xs").style("color: var(--lp-muted)")

        create_title = ui.input("Title").props("clearable").classes("w-full")
        create_description = ui.textarea("Description").props("autogrow").classes("w-full")
        create_provider = ui.input("Provider").props("clearable").classes("w-full")
        create_category = ui.input("Category").props("clearable").classes("w-full")
        create_url = ui.input("URL").props("clearable").classes("w-full")
        create_language = ui.input("Language").props("clearable").classes("w-full")

        with ui.expansion("More fields").props("dense"):
            with ui.column().classes("w-full gap-3"):
                create_level = ui.input("Level").props("clearable").classes("w-full")
                create_learning_outcomes = ui.textarea("Learning outcomes (optional)").props("autogrow").classes("w-full")
                create_prerequisites = ui.textarea("Prerequisites (optional)").props("autogrow").classes("w-full")
                create_duration_hours = ui.input("Duration hours").props("clearable").classes("w-full")

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

        def _apply_course_draft(raw: Any) -> None:
            draft = raw if isinstance(raw, dict) else {}
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

        with ui.row().classes("justify-end mt-4"):

            def _save_draft() -> None:
                app.storage.user[course_draft_key] = _course_draft_payload()
                safe_notify("Draft saved", type="positive")

            def _load_draft() -> None:
                draft = app.storage.user.get(course_draft_key)
                if not isinstance(draft, dict):
                    safe_notify("No saved draft found", type="warning")
                    return
                _apply_course_draft(draft)
                safe_notify("Draft loaded", type="positive")

            @guard_ui_action(title="Share course failed")
            async def _create_submit() -> None:
                dh_raw = str(create_duration_hours.value or "")
                dh = parse_duration_hours(dh_raw)
                if dh_raw.strip() and dh is None:
                    safe_notify("Duration hours must be a number", type="negative")
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
                await on_submit(payload)
                app.storage.user.pop(course_draft_key, None)
                safe_notify("Course shared", type="positive")
                create_dialog.close()

            ui.button("Save draft", on_click=_save_draft).props("outline")
            ui.button("Load draft", on_click=_load_draft).props("outline")
            ui.button("Share", on_click=_create_submit)
            ui.button("Cancel", on_click=create_dialog.close).props("outline")

    def _open_create_dialog() -> None:
        _apply_course_draft(app.storage.user.get(course_draft_key))
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
