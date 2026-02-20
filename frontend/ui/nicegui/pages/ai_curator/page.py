"""AI Curator page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.ai_curator.controller import AiCuratorPageController
from frontend.ui.nicegui.pages.ai_curator.state import AiCuratorPageState
from frontend.ui.nicegui.pages.ai_curator.transitions import begin_apply, begin_generate, finalize_apply, finalize_generate


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

        is_admin = str(user.get("role") or "") == "admin"
        controller = AiCuratorPageController(api=api)
        state = AiCuratorPageState()

        render_shell(title="AI Curator", store=store, api=api)
        with render_container():
            ui.label("Generate a draft learning path from a goal.").classes("text-sm text-gray-600")

            goal = ui.input("Goal").props("clearable").classes("w-full")
            meta = ui.label("").classes("text-sm text-gray-600")

            path_name = ui.input("Draft path name").props("clearable").classes("w-full")
            path_description = ui.textarea("Draft path description").props("autogrow").classes("w-full")
            select_for_me = ui.checkbox("Select created path for me (after apply)", value=True)

            @ui.refreshable
            def courses_preview() -> None:
                with ui.column().classes("w-full gap-3"):
                    if not state.draft_courses:
                        ui.label("No draft yet. Enter a goal and click Generate.").classes("text-sm text-gray-600")
                        return

                    for idx, c in enumerate(list(state.draft_courses)):
                        title = str(c.get("title") or "")
                        description = str(c.get("description") or "")
                        provider = str(c.get("provider") or "")
                        category = str(c.get("category") or "")
                        level = str(c.get("level") or "")
                        url = str(c.get("url") or "")

                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    ui.label(f"{idx + 1}. {title}").classes("text-lg font-semibold")
                                    if description:
                                        ui.label(description).classes("text-sm text-gray-600")
                                    ui.label(f"{provider} · {category} · {level}").classes("text-sm text-gray-600")
                                    if url:
                                        ui.link("Open resource", url).props("target=_blank").classes("text-sm")

                                with ui.row().classes("items-center"):

                                    def _move_up(i: int = idx) -> None:
                                        if i <= 0:
                                            return
                                        state.draft_courses[i - 1], state.draft_courses[i] = (
                                            state.draft_courses[i],
                                            state.draft_courses[i - 1],
                                        )
                                        courses_preview.refresh()

                                    def _move_down(i: int = idx) -> None:
                                        if i >= len(state.draft_courses) - 1:
                                            return
                                        state.draft_courses[i + 1], state.draft_courses[i] = (
                                            state.draft_courses[i],
                                            state.draft_courses[i + 1],
                                        )
                                        courses_preview.refresh()

                                    def _remove(i: int = idx) -> None:
                                        if 0 <= i < len(state.draft_courses):
                                            state.draft_courses.pop(i)
                                            courses_preview.refresh()

                                    def _edit(i: int = idx) -> None:
                                        current = state.draft_courses[i]
                                        with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
                                            ui.label("Edit draft course").classes("text-xl font-semibold")
                                            t = ui.input("Title", value=str(current.get("title") or "")).classes("w-full")
                                            d = (
                                                ui.textarea("Description", value=str(current.get("description") or ""))
                                                .props("autogrow")
                                                .classes("w-full")
                                            )
                                            p = ui.input("Provider", value=str(current.get("provider") or "")).classes("w-full")
                                            cat = ui.input("Category", value=str(current.get("category") or "")).classes(
                                                "w-full"
                                            )
                                            lvl = ui.input("Level", value=str(current.get("level") or "")).classes("w-full")
                                            u = ui.input("URL", value=str(current.get("url") or "")).classes("w-full")
                                            with ui.row().classes("justify-end mt-4"):

                                                def _save() -> None:
                                                    current["title"] = str(t.value or "").strip()
                                                    current["description"] = str(d.value or "").strip()
                                                    current["provider"] = str(p.value or "").strip()
                                                    current["category"] = str(cat.value or "").strip()
                                                    current["level"] = str(lvl.value or "").strip()
                                                    current["url"] = str(u.value or "").strip()
                                                    courses_preview.refresh()
                                                    dialog.close()

                                                ui.button("Save", on_click=_save)
                                                ui.button("Cancel", on_click=dialog.close).props("outline")
                                        dialog.open()

                                    ui.button("Up", on_click=_move_up).props("dense outline")
                                    ui.button("Down", on_click=_move_down).props("dense outline")
                                    ui.button("Edit", on_click=_edit).props("dense outline")
                                    ui.button("Remove", on_click=_remove).props("dense color=negative outline")

            @guard_ui_action(title="Plan generation failed")
            async def _generate() -> None:
                g = str(goal.value or "").strip()
                if not g:
                    ui.notify("Goal is required.", type="negative")
                    return
                if state.generating:
                    return
                start = begin_generate()
                state.generating = start.generating
                generate_btn.disable()
                apply_btn.disable()
                meta.text = start.meta_text
                try:
                    path, courses = await controller.generate_plan(goal=g)
                    state.draft_courses = list(courses or [])
                    path_name.value = str(path.get("name") or "")
                    path_description.value = str(path.get("description") or "")
                    courses_preview.refresh()
                    done = finalize_generate(count=len(state.draft_courses))
                    meta.text = done.meta_text
                except Exception:
                    meta.text = "Generation failed"
                    raise
                finally:
                    state.generating = False
                    generate_btn.enable()
                    if is_admin and state.draft_courses and not state.applying:
                        apply_btn.enable()

            @guard_ui_action(title="Apply plan failed")
            async def _apply() -> None:
                if not is_admin:
                    ui.notify("Admin required to apply a draft.", type="negative")
                    return
                if not state.draft_courses:
                    ui.notify("Generate a draft first.", type="negative")
                    return
                if state.applying:
                    return

                start = begin_apply()
                state.applying = start.applying
                apply_btn.disable()
                meta.text = start.meta_text
                try:
                    await controller.apply_plan(
                        draft_courses=state.draft_courses,
                        path_name=str(path_name.value or ""),
                        path_description=str(path_description.value or ""),
                        select_for_me=bool(select_for_me.value),
                    )
                    ui.notify("Draft applied: courses + path created.", type="positive")
                    done = finalize_apply()
                    meta.text = done.meta_text
                except Exception:
                    meta.text = "Apply failed"
                    raise
                finally:
                    state.applying = False
                    apply_btn.enable()

            with ui.row().classes("items-center gap-2"):
                generate_btn = ui.button("Generate", on_click=_generate).props("outline")
                apply_btn = ui.button("Apply (create)", on_click=_apply).props("color=positive")
                if not is_admin:
                    apply_btn.disable()

            ui.separator()
            ui.label("Draft preview").classes("text-lg font-semibold")
            courses_preview()
