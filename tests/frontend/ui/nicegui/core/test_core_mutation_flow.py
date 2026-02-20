from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.mutation_flow import run_optimistic_mutation


@pytest.mark.anyio
async def test_run_optimistic_mutation_success_path() -> None:
    events: list[str] = []

    async def _perform() -> bool:
        events.append("perform")
        return True

    ok = await run_optimistic_mutation(
        apply_optimistic=lambda: events.append("apply") or {"snapshot": True},
        perform_mutation=_perform,
        rollback=lambda _snapshot: events.append("rollback"),
        refresh_ui=lambda: events.append("refresh"),
        on_success=lambda: events.append("success"),
    )
    assert ok is True
    assert events == ["apply", "refresh", "perform", "success"]


@pytest.mark.anyio
async def test_run_optimistic_mutation_rolls_back_when_perform_returns_false() -> None:
    events: list[str] = []

    async def _perform() -> bool:
        events.append("perform")
        return False

    ok = await run_optimistic_mutation(
        apply_optimistic=lambda: events.append("apply") or {"snapshot": True},
        perform_mutation=_perform,
        rollback=lambda _snapshot: events.append("rollback"),
        refresh_ui=lambda: events.append("refresh"),
    )
    assert ok is False
    assert events == ["apply", "refresh", "perform", "rollback", "refresh"]


@pytest.mark.anyio
async def test_run_optimistic_mutation_rolls_back_and_reraises_on_exception() -> None:
    events: list[str] = []

    async def _perform() -> bool:
        events.append("perform")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await run_optimistic_mutation(
            apply_optimistic=lambda: events.append("apply") or {"snapshot": True},
            perform_mutation=_perform,
            rollback=lambda _snapshot: events.append("rollback"),
            refresh_ui=lambda: events.append("refresh"),
        )
    assert events == ["apply", "refresh", "perform", "rollback", "refresh"]
