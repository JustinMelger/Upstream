"""Card-level actions for the Paths page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify


@dataclass(slots=True)
class PathCardActions:
    """Callback bundle for a single path card."""

    on_review: Callable[[], Awaitable[None]]
    on_recommend: Callable[[], Awaitable[None]]
    on_copy_link: Callable[[], None]
    on_edit: Callable[[], Awaitable[None]]
    on_delete: Callable[[], Awaitable[None]]
    on_view: Callable[[], Awaitable[None]]
    on_track_toggle: Callable[[], Awaitable[None]]
    track_toggle_label: str


@dataclass(slots=True)
class PathsFilterControls:
    """UI controls used by filter-clear/reset handlers."""

    scope_filter: Any
    search_input: Any
    status_filter: Any | None
    sort_filter: Any


def path_share_link(*, path_id: int) -> str:
    """Build a copyable app-relative deep link for a path."""
    return f"/paths?path_id={int(path_id)}&view=full"


def copy_path_link(*, path_id: int) -> None:
    """Copy a deep link for a path to the clipboard."""
    link = path_share_link(path_id=int(path_id))
    ui.run_javascript(f"navigator.clipboard.writeText(window.location.origin + {repr(link)});")
    safe_notify("Link copied", type="positive")


def build_track_toggle(
    *,
    path_id: int,
    is_tracked: bool,
    on_select: Callable[[int], Awaitable[bool | None]],
    on_unselect: Callable[[int], Awaitable[bool | None]],
    on_after_toggle: Callable[[], None] | None = None,
) -> tuple[Callable[[], Awaitable[None]], str]:
    """Return card toggle handler + button label for tracked/untracked state."""
    if is_tracked:

        async def _do_unselect() -> None:
            ok = await on_unselect(int(path_id))
            if ok is True and on_after_toggle is not None:
                on_after_toggle()

        return _do_unselect, "Untrack"

    async def _do_select() -> None:
        ok = await on_select(int(path_id))
        if ok is True and on_after_toggle is not None:
            on_after_toggle()

    return _do_select, "Track"


async def open_recommend_dialog(
    *,
    path_id: int,
    username: str,
    get_user_note: Callable[[int, str], Awaitable[str]],
    save_recommendation: Callable[[int, str], Awaitable[dict[str, Any]]],
    on_saved: Callable[[], Awaitable[None]],
) -> None:
    """Open recommend dialog for a path and persist recommendation."""
    existing_note = ""
    try:
        existing_note = await get_user_note(int(path_id), username)
    except Exception:
        existing_note = ""

    with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(600px,95vw)]"):
        ui.label("Recommend path").classes("text-lg font-semibold")
        note = ui.textarea("Why this helps (optional)", value=existing_note).props("autogrow").classes("w-full")
        with ui.row().classes("justify-end mt-4"):

            @guard_ui_action(title="Recommend failed")
            async def _save() -> None:
                await save_recommendation(int(path_id), str(note.value or ""))
                safe_notify("Recommendation saved", type="positive")
                dialog.close()
                await on_saved()

            ui.button("Save", on_click=_save)
            ui.button("Cancel", on_click=dialog.close).props("outline")

    dialog.open()


def build_path_card_actions(
    *,
    path_id: int,
    is_tracked: bool,
    username: str,
    get_user_note: Callable[[int, str], Awaitable[str]],
    save_recommendation: Callable[[int, str], Awaitable[dict[str, Any]]],
    on_saved: Callable[[], Awaitable[None]],
    get_path_detail: Callable[[int], Awaitable[dict[str, Any]]],
    on_open_edit: Callable[[int, dict[str, Any]], Awaitable[None]],
    on_delete: Callable[[int], Awaitable[None]],
    on_open_details: Callable[[int, str], Awaitable[None]],
    on_select: Callable[[int], Awaitable[bool | None]],
    on_unselect: Callable[[int], Awaitable[bool | None]],
    on_after_toggle: Callable[[], None] | None = None,
) -> PathCardActions:
    """Build per-card callbacks to keep page view logic minimal."""

    async def _recommend() -> None:
        await open_recommend_dialog(
            path_id=int(path_id),
            username=username,
            get_user_note=get_user_note,
            save_recommendation=save_recommendation,
            on_saved=on_saved,
        )

    def _copy_link() -> None:
        copy_path_link(path_id=int(path_id))

    async def _review() -> None:
        await on_open_details(int(path_id), "reviews")

    async def _edit() -> None:
        detail = await get_path_detail(int(path_id))
        await on_open_edit(int(path_id), detail)

    async def _delete() -> None:
        await on_delete(int(path_id))

    async def _view() -> None:
        await on_open_details(int(path_id), "full")

    on_track_toggle, track_toggle_label = build_track_toggle(
        path_id=int(path_id),
        is_tracked=is_tracked,
        on_select=on_select,
        on_unselect=on_unselect,
        on_after_toggle=on_after_toggle,
    )

    return PathCardActions(
        on_review=_review,
        on_recommend=_recommend,
        on_copy_link=_copy_link,
        on_edit=_edit,
        on_delete=_delete,
        on_view=_view,
        on_track_toggle=on_track_toggle,
        track_toggle_label=track_toggle_label,
    )


def clear_path_filter_by_key(*, key: str, controls: PathsFilterControls) -> bool:
    """Clear a single path filter key and update its control."""
    k = str(key or "")
    if k == "scope":
        controls.scope_filter.value = "all"
        controls.scope_filter.update()
        return True
    if k == "search":
        controls.search_input.value = ""
        controls.search_input.update()
        return True
    if k == "status":
        if controls.status_filter is None:
            return False
        controls.status_filter.value = ""
        controls.status_filter.update()
        return True
    if k == "sort":
        controls.sort_filter.value = ""
        controls.sort_filter.update()
        return True
    return False


def reset_path_filter_controls(*, controls: PathsFilterControls) -> None:
    """Reset all path filter controls to defaults and update them."""
    controls.search_input.value = ""
    controls.search_input.update()
    if controls.status_filter is not None:
        controls.status_filter.value = ""
        controls.status_filter.update()
    controls.sort_filter.value = ""
    controls.sort_filter.update()
    controls.scope_filter.value = "all"
    controls.scope_filter.update()
