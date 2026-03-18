"""AI Curator page for the NiceGUI frontend."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.ai_curator.controller import AiCuratorPageController
from frontend.ui.nicegui.pages.ai_curator.state import AiCuratorPageState
from frontend.ui.nicegui.pages.ai_curator.transitions import begin_apply, begin_generate, finalize_apply, finalize_generate


@dataclass(slots=True)
class AiCuratorControls:
    """UI handles used by the AI Curator page actions."""

    goal: Any
    meta: Any
    path_name: Any
    path_description: Any
    select_for_me: Any
    generate_btn: Any | None = None
    apply_btn: Any | None = None
    courses_preview: Any | None = None


@dataclass(slots=True)
class AiCuratorPageContext:
    """Mutable page context shared across UI helpers."""

    controller: AiCuratorPageController
    state: AiCuratorPageState
    controls: AiCuratorControls
    is_admin: bool


def _refresh_courses_preview(ctx: AiCuratorPageContext) -> None:
    preview = ctx.controls.courses_preview
    if preview is not None:
        preview.refresh()


def _sync_action_buttons(ctx: AiCuratorPageContext) -> None:
    generate_btn = ctx.controls.generate_btn
    apply_btn = ctx.controls.apply_btn
    if generate_btn is not None:
        if ctx.state.generating:
            generate_btn.disable()
        else:
            generate_btn.enable()
    if apply_btn is not None:
        can_apply = ctx.is_admin and bool(ctx.state.draft_courses) and not ctx.state.applying
        if can_apply:
            apply_btn.enable()
        else:
            apply_btn.disable()


def _move_draft_course(ctx: AiCuratorPageContext, *, index: int, offset: int) -> None:
    next_index = index + offset
    if index < 0 or next_index < 0 or next_index >= len(ctx.state.draft_courses):
        return
    ctx.state.draft_courses[index], ctx.state.draft_courses[next_index] = (
        ctx.state.draft_courses[next_index],
        ctx.state.draft_courses[index],
    )
    _refresh_courses_preview(ctx)


def _remove_draft_course(ctx: AiCuratorPageContext, *, index: int) -> None:
    if 0 <= index < len(ctx.state.draft_courses):
        ctx.state.draft_courses.pop(index)
        _refresh_courses_preview(ctx)
        _sync_action_buttons(ctx)


def _save_draft_course_edits(
    current: dict[str, Any],
    *,
    title: Any,
    description: Any,
    provider: Any,
    category: Any,
    level: Any,
    url: Any,
    dialog: Any,
    ctx: AiCuratorPageContext,
) -> None:
    current["title"] = str(title.value or "").strip()
    current["description"] = str(description.value or "").strip()
    current["provider"] = str(provider.value or "").strip()
    current["category"] = str(category.value or "").strip()
    current["level"] = str(level.value or "").strip()
    current["url"] = str(url.value or "").strip()
    _refresh_courses_preview(ctx)
    dialog.close()


def _open_edit_draft_course_dialog(ctx: AiCuratorPageContext, *, index: int) -> None:
    current = ctx.state.draft_courses[index]
    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
        ui.label("Edit draft course").classes("text-xl font-semibold")
        title = ui.input("Title", value=str(current.get("title") or "")).classes("w-full")
        description = (
            ui.textarea("Description", value=str(current.get("description") or "")).props("autogrow").classes("w-full")
        )
        provider = ui.input("Provider", value=str(current.get("provider") or "")).classes("w-full")
        category = ui.input("Category", value=str(current.get("category") or "")).classes("w-full")
        level = ui.input("Level", value=str(current.get("level") or "")).classes("w-full")
        url = ui.input("URL", value=str(current.get("url") or "")).classes("w-full")
        with ui.row().classes("justify-end mt-4"):
            ui.button(
                "Save",
                on_click=partial(
                    _save_draft_course_edits,
                    current,
                    title=title,
                    description=description,
                    provider=provider,
                    category=category,
                    level=level,
                    url=url,
                    dialog=dialog,
                    ctx=ctx,
                ),
            )
            ui.button("Cancel", on_click=dialog.close).props("outline")
    dialog.open()


def _render_draft_course_actions(ctx: AiCuratorPageContext, *, index: int) -> None:
    with ui.row().classes("items-center"):
        ui.button("Up", on_click=partial(_move_draft_course, ctx, index=index, offset=-1)).props("dense outline")
        ui.button("Down", on_click=partial(_move_draft_course, ctx, index=index, offset=1)).props("dense outline")
        ui.button("Edit", on_click=partial(_open_edit_draft_course_dialog, ctx, index=index)).props("dense outline")
        ui.button("Remove", on_click=partial(_remove_draft_course, ctx, index=index)).props("dense color=negative outline")


def _render_draft_course_card(ctx: AiCuratorPageContext, *, index: int, course: dict[str, Any]) -> None:
    title = str(course.get("title") or "")
    description = str(course.get("description") or "")
    provider = str(course.get("provider") or "")
    category = str(course.get("category") or "")
    level = str(course.get("level") or "")
    url = str(course.get("url") or "")

    with ui.card().classes("w-full"):
        with ui.row().classes("items-start justify-between w-full"):
            with ui.column().classes("gap-1"):
                ui.label(f"{index + 1}. {title}").classes("text-lg font-semibold")
                if description:
                    ui.label(description).classes("text-sm text-gray-600")
                ui.label(f"{provider} · {category} · {level}").classes("text-sm text-gray-600")
                if url:
                    ui.link("Open resource", url).props("target=_blank").classes("text-sm")
            _render_draft_course_actions(ctx, index=index)


def _render_courses_preview(ctx: AiCuratorPageContext) -> None:
    with ui.column().classes("w-full gap-3"):
        if not ctx.state.draft_courses:
            ui.label("No draft yet. Enter a goal and click Generate.").classes("text-sm text-gray-600")
            return
        for index, course in enumerate(list(ctx.state.draft_courses)):
            _render_draft_course_card(ctx, index=index, course=course)


async def _generate_draft(ctx: AiCuratorPageContext) -> None:
    goal = str(ctx.controls.goal.value or "").strip()
    if not goal:
        safe_notify("Goal is required.", type="negative")
        return
    if ctx.state.generating:
        return

    start = begin_generate()
    ctx.state.generating = start.generating
    ctx.controls.meta.text = start.meta_text
    _sync_action_buttons(ctx)
    try:
        path, courses = await ctx.controller.generate_plan(goal=goal)
        ctx.state.draft_courses = list(courses or [])
        ctx.controls.path_name.value = str(path.get("name") or "")
        ctx.controls.path_description.value = str(path.get("description") or "")
        _refresh_courses_preview(ctx)
        ctx.controls.meta.text = finalize_generate(count=len(ctx.state.draft_courses)).meta_text
    except (ApiError, RuntimeError):
        ctx.controls.meta.text = "Generation failed"
        raise
    finally:
        ctx.state.generating = False
        _sync_action_buttons(ctx)


async def _apply_draft(ctx: AiCuratorPageContext) -> None:
    if not ctx.is_admin:
        safe_notify("Admin required to apply a draft.", type="negative")
        return
    if not ctx.state.draft_courses:
        safe_notify("Generate a draft first.", type="negative")
        return
    if ctx.state.applying:
        return

    start = begin_apply()
    ctx.state.applying = start.applying
    ctx.controls.meta.text = start.meta_text
    _sync_action_buttons(ctx)
    try:
        await ctx.controller.apply_plan(
            draft_courses=ctx.state.draft_courses,
            path_name=str(ctx.controls.path_name.value or ""),
            path_description=str(ctx.controls.path_description.value or ""),
            select_for_me=bool(ctx.controls.select_for_me.value),
        )
        safe_notify("Draft applied: courses + path created.", type="positive")
        ctx.controls.meta.text = finalize_apply().meta_text
    except (ApiError, RuntimeError):
        ctx.controls.meta.text = "Apply failed"
        raise
    finally:
        ctx.state.applying = False
        _sync_action_buttons(ctx)


def _build_ai_curator_controls() -> AiCuratorControls:
    goal = ui.input("Goal").props("clearable").classes("w-full")
    meta = ui.label("").classes("text-sm text-gray-600")
    path_name = ui.input("Draft path name").props("clearable").classes("w-full")
    path_description = ui.textarea("Draft path description").props("autogrow").classes("w-full")
    select_for_me = ui.checkbox("Select created path for me (after apply)", value=True)
    return AiCuratorControls(
        goal=goal,
        meta=meta,
        path_name=path_name,
        path_description=path_description,
        select_for_me=select_for_me,
    )


def _render_action_row(ctx: AiCuratorPageContext) -> None:
    @guard_ui_action(title="Plan generation failed")
    async def _on_generate() -> None:
        await _generate_draft(ctx)

    @guard_ui_action(title="Apply plan failed")
    async def _on_apply() -> None:
        await _apply_draft(ctx)

    with ui.row().classes("items-center gap-2"):
        ctx.controls.generate_btn = ui.button("Generate", on_click=_on_generate).props("outline")
        ctx.controls.apply_btn = ui.button("Apply (create)", on_click=_on_apply).props("color=positive")
    _sync_action_buttons(ctx)


def _render_ai_curator_body(ctx: AiCuratorPageContext) -> None:
    ui.label("Generate a draft learning path from a goal.").classes("text-sm text-gray-600")
    ui.separator()

    ctx.controls = _build_ai_curator_controls()

    @ui.refreshable
    def courses_preview() -> None:
        _render_courses_preview(ctx)

    ctx.controls.courses_preview = courses_preview
    _render_action_row(ctx)
    ui.separator()
    ui.label("Draft preview").classes("text-lg font-semibold")
    courses_preview()


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/ai` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/ai")
    async def ai_curator_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        ctx = AiCuratorPageContext(
            controller=AiCuratorPageController(api=api),
            state=AiCuratorPageState(),
            controls=AiCuratorControls(goal=None, meta=None, path_name=None, path_description=None, select_for_me=None),
            is_admin=str(user.get("role") or "") == "admin",
        )
        render_shell(title="AI Curator", store=store, api=api)
        with render_container():
            _render_ai_curator_body(ctx)
