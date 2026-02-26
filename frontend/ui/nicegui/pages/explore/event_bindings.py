"""Event-binding helpers for Explore page controls."""

from __future__ import annotations

from typing import Any


def bind_refresh_events(
    *,
    topbar: Any,
    filter_controls: Any,
    on_search_change: Any,
    on_refresh: Any,
) -> None:
    """Bind Explore topbar/filter control updates to refresh callbacks."""
    topbar.search_input.on("update:model-value", on_search_change)
    topbar.tab_filter.on("update:model-value", lambda *_: on_refresh())
    topbar.sort_filter.on("update:model-value", lambda *_: on_refresh())

    for control in [
        filter_controls.provider_filter,
        filter_controls.category_filter,
        filter_controls.tag_filter,
        filter_controls.author_filter,
    ]:
        control.on("update:model-value", lambda *_: on_refresh())
