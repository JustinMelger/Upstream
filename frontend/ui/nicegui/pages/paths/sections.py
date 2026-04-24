"""UI sections for the Paths page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.components.path_card import PathCardCallbacks, PathCardDisplay, render_path_card
from frontend.ui.nicegui.pages.paths.actions import build_path_card_actions, PathCardActionDeps
from frontend.ui.nicegui.pages.paths.dialogs import open_edit_path_dialog
from frontend.ui.nicegui.pages.paths.orchestration import perform_update_path
from frontend.ui.nicegui.pages.paths.state import PathsPageState, PathsPageUiState
from frontend.ui.nicegui.pages.paths.ui_glue import compute_expanded_visible_count
from frontend.ui.nicegui.pages.paths.view_model import map_path_card_view


@dataclass(frozen=True, slots=True)
class PathsCardsRenderDeps:
    """Dependencies for rendering path cards list and actions."""

    username: str
    is_admin: bool
    controller: Any
    controller_state: PathsPageState
    ui_state: PathsPageUiState
    refresh_paths_list_ui: Callable[[], None]
    recompute_facet_options: Callable[[], None]
    open_details: Callable[[int, str], Awaitable[None]]
    select_path: Callable[[int], Awaitable[bool | None]]
    unselect_path: Callable[[int], Awaitable[bool | None]]
    delete_path: Callable[[int], Awaitable[None]]
    load_all: Callable[[], Awaitable[None]]


def render_paths_cards_block(
    *,
    shown: list[dict[str, Any]],
    deps: PathsCardsRenderDeps,
) -> None:
    """Render paged path cards with per-card actions."""
    total = len(shown)
    shown_page = shown[: max(0, int(deps.ui_state.visible_count))]
    for path_row in shown_page:
        path_id = int(path_row.get("id") or 0)
        selected = deps.controller_state.selected_by_id.get(path_id)
        can_edit = deps.is_admin or (str(path_row.get("created_by") or "") == deps.username)
        is_tracked = selected is not None
        detail = deps.controller_state.selected_detail_by_path_id.get(path_id) if selected else None
        card_vm = map_path_card_view(
            path_row=path_row,
            is_tracked=is_tracked,
            detail=detail if isinstance(detail, dict) else None,
            tracking_by_course_id=deps.controller_state.tracking_by_course_id,
            review_summary_row=deps.controller_state.path_review_summary_by_id.get(path_id),
        )
        actions = build_path_card_actions(
            path_id=path_id,
            is_tracked=is_tracked,
            deps=PathCardActionDeps(
                get_path_detail=lambda _pid: deps.controller.get_path_detail(path_id=int(_pid)),
                on_open_edit=lambda _pid, _detail: open_edit_path_dialog(
                    detail=_detail,
                    learning_item_options=deps.controller_state.learning_item_options,
                    detail_dialog=None,
                    on_save=partial(
                        perform_update_path,
                        path_id=int(_pid),
                        controller=deps.controller,
                        reload_page=deps.load_all,
                        refresh_paths_list_ui=deps.refresh_paths_list_ui,
                    ),
                ),
                on_delete=deps.delete_path,
                on_open_details=lambda _pid, _mode: deps.open_details(_pid, _mode),
                on_select=deps.select_path,
                on_unselect=deps.unselect_path,
            ),
            on_after_toggle=deps.recompute_facet_options,
        )
        render_path_card(
            display=PathCardDisplay(
                path_row=path_row,
                card_class_suffix=card_vm.card_class_suffix,
                is_new=card_vm.is_new,
                is_updated=card_vm.is_updated,
                rating_badge=card_vm.rating_badge,
                can_edit=can_edit,
                is_tracked=is_tracked,
                shared_by=card_vm.shared_by,
                tracking_label_text=card_vm.tracking_label_text,
                tracking_chip_cls=card_vm.tracking_chip_cls,
                completed=card_vm.completed,
                total_courses=card_vm.total_courses,
                progress=card_vm.progress,
                milestone=card_vm.milestone,
                milestone_class=card_vm.milestone_class,
                impact=card_vm.impact,
                next_title=card_vm.next_title,
            ),
            actions=PathCardCallbacks(
                on_review=actions.on_review,
                on_copy_link=actions.on_copy_link,
                on_edit=actions.on_edit,
                on_delete=actions.on_delete,
                on_view=actions.on_view,
                on_track_toggle=actions.on_track_toggle,
                track_toggle_label=actions.track_toggle_label,
            ),
        )

    if total > len(shown_page):

        def _load_more() -> None:
            deps.ui_state.visible_count = compute_expanded_visible_count(
                current_visible=int(deps.ui_state.visible_count),
                total_count=int(total),
                page_size=int(deps.ui_state.page_size),
            )
            deps.refresh_paths_list_ui()

        render_load_more_footer(
            shown_page_count=len(shown_page),
            shown_total_count=total,
            on_load_more=_load_more,
        )


def render_paths_active_filter_chips(*, chips: list[Any], on_clear_key: Any) -> None:
    """Render removable active-filter chips for Paths."""
    if not chips:
        return

    with ui.row().classes("items-center gap-2 w-full"):
        for chip in chips:
            with ui.row().classes("items-center"):
                with ui.element("div").classes("lp-filter-chip"):
                    ui.label(str(chip.label or ""))
                    ui.button("×", on_click=lambda _key=chip.key: on_clear_key(str(_key))).props("dense flat")


def render_paths_empty_state(
    *,
    empty_state: str,
    on_browse_all: Any,
    on_refresh: Any,
    on_share: Any,
    on_browse_courses: Any,
    on_reset_all: Any,
) -> bool:
    """Render the matching empty-state block and return whether one was rendered."""
    _ = on_refresh
    _ = on_browse_courses
    if empty_state == "selected_empty":
        ui.label("No selected path yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Browse and select a path to start milestone progress.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Browse all paths", on_click=on_browse_all).props("outline")
        return True

    if empty_state == "catalog_empty":
        ui.label("No path library yet.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Share a path to create your team learning roadmap.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Share a path", on_click=on_share).props("outline")
        return True

    if empty_state == "filters_empty":
        ui.label("No paths match this filter set.").classes("text-sm").style("color: var(--lp-muted)")
        ui.label("Reset filters to see more path options.").classes("text-sm").style("color: var(--lp-muted)")
        with ui.row().classes("items-center gap-2"):
            ui.button("Reset all", on_click=on_reset_all).props("outline")
        return True

    return False


def render_paths_collection_intro() -> None:
    """Render section heading above the paths result list."""
    with ui.column().classes("w-full gap-1 lp-courses-section"):
        ui.label("Learning paths").classes("lp-courses-section-title")
        ui.label("Structured journeys your team shared to build momentum").classes("lp-courses-section-subtitle")
