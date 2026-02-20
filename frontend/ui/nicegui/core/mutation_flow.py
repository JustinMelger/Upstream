"""Shared optimistic mutation flow helpers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar


TSnapshot = TypeVar("TSnapshot")


async def run_optimistic_mutation(
    *,
    apply_optimistic: Callable[[], TSnapshot],
    perform_mutation: Callable[[], Awaitable[bool]],
    rollback: Callable[[TSnapshot], None],
    refresh_ui: Callable[[], None],
    on_success: Callable[[], None] | None = None,
) -> bool:
    """Run a standardized optimistic mutation flow.

    Flow:
    1. Apply optimistic local state and refresh UI.
    2. Execute async mutation.
    3. If mutation reports failure, rollback and refresh.
    4. On exception, rollback and refresh, then re-raise.
    5. On success, run optional success callback.
    """
    snapshot = apply_optimistic()
    refresh_ui()
    try:
        ok = bool(await perform_mutation())
        if not ok:
            rollback(snapshot)
            refresh_ui()
            return False
    except Exception:
        rollback(snapshot)
        refresh_ui()
        raise

    if callable(on_success):
        on_success()
    return True
