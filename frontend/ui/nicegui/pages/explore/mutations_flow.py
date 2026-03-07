"""Mutation handler builders for Explore page actions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.state import ExplorePageState


@dataclass(frozen=True, slots=True)
class ExploreMutationHandlers:
    """Async mutation handlers used by Explore list and card actions."""

    set_tracking: Callable[[int, str], Awaitable[None]]
    clear_tracking: Callable[[int], Awaitable[None]]
    toggle_path_selection: Callable[[int], Awaitable[None]]


def build_mutation_handlers(
    *,
    controller: ExplorePageController,
    state: ExplorePageState,
    refresh_ui: Callable[..., Any],
) -> ExploreMutationHandlers:
    """Build async handlers that call the Explore controller with shared deps."""

    async def _set_tracking(course_id: int, status: str) -> None:
        await controller.set_tracking_status(
            state=state,
            course_id=int(course_id),
            status=str(status),
            refresh_ui=refresh_ui,
        )

    async def _clear_tracking(course_id: int) -> None:
        await controller.clear_tracking_status(
            state=state,
            course_id=int(course_id),
            refresh_ui=refresh_ui,
        )

    async def _toggle_path_selection(path_id: int) -> None:
        await controller.toggle_path_selection(
            state=state,
            path_id=int(path_id),
            refresh_ui=refresh_ui,
        )

    return ExploreMutationHandlers(
        set_tracking=_set_tracking,
        clear_tracking=_clear_tracking,
        toggle_path_selection=_toggle_path_selection,
    )
