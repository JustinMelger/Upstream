"""Explore share routing extracted from page composition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExploreShareBindings:
    """Share callbacks wired for Explore share menu targets."""

    open_share_target: Callable[[str], None]


def create_explore_share_bindings(
    *,
    on_open_learning_item_share_page: Callable[[], None],
    on_open_path_share_page: Callable[[], None],
    on_unknown_target: Callable[[str], None],
) -> ExploreShareBindings:
    """Create share callbacks used by the Explore page."""

    def _open_share_target(target: str) -> None:
        tab = str(target or "").strip().lower()
        if tab == "learning_item":
            on_open_learning_item_share_page()
            return
        if tab == "path":
            on_open_path_share_page()
            return
        on_unknown_target(tab)

    return ExploreShareBindings(open_share_target=_open_share_target)
