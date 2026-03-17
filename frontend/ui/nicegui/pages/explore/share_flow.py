"""Explore share dialog wiring extracted from page composition."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.share_models import ExploreSharePayload
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.paths.dialogs import build_share_path_dialog


@dataclass(frozen=True, slots=True)
class ExploreShareBindings:
    """Share callbacks wired for Explore share menu targets."""

    open_share_target: Callable[[str], None]


def create_explore_share_bindings(
    *,
    controller: ExplorePageController,
    state: ExplorePageState,
    username: str,
    reload_data: Callable[[], Awaitable[None]],
    refresh_ui: Callable[..., Any],
    on_open_video_share_page: Callable[[], None],
    on_open_course_share_page: Callable[[], None],
    on_open_article_share_page: Callable[[], None],
    on_unknown_target: Callable[[str], None],
) -> ExploreShareBindings:
    """Create share callbacks and dialog openers used by Explore page."""

    async def _submit_path_share(payload: dict[str, Any]) -> None:
        await controller.create_path_share(
            state=state,
            payload=ExploreSharePayload(payload=dict(payload or {})),
            reload_data=reload_data,
            refresh_ui=refresh_ui,
        )

    path_share_dialog, path_share_course_ids, open_path_share_dialog_raw = build_share_path_dialog(
        username=username,
        on_submit=_submit_path_share,
    )
    _ = path_share_dialog

    def _open_path_share_dialog() -> None:
        path_share_course_ids.options = controller.build_path_share_course_options(state=state)
        path_share_course_ids.update()
        open_path_share_dialog_raw()

    def _open_share_target(target: str) -> None:
        tab = str(target or "").strip().lower()
        if tab == "video":
            on_open_video_share_page()
            return
        if tab == "course":
            on_open_course_share_page()
            return
        if tab == "path":
            _open_path_share_dialog()
            return
        if tab == "article":
            on_open_article_share_page()
            return
        on_unknown_target(tab)

    return ExploreShareBindings(open_share_target=_open_share_target)
