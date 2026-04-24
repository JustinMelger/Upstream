from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.shared_stats.state import SharedStatsState


async def _trigger_load(*, state: SharedStatsState, run_once) -> None:  # noqa: ANN001
    if state.loading:
        state.pending_reload = True
        return
    state.loading = True
    state.pending_reload = False
    try:
        await run_once()
    finally:
        state.loading = False
        if state.pending_reload:
            state.pending_reload = False
            await _trigger_load(state=state, run_once=run_once)


@pytest.mark.anyio
async def test_home_load_queue_runs_one_followup_when_requested_mid_load() -> None:
    state = SharedStatsState()
    runs = 0

    async def _run_once() -> None:
        nonlocal runs
        runs += 1
        if runs == 1:
            await _trigger_load(state=state, run_once=_run_once)

    await _trigger_load(state=state, run_once=_run_once)
    assert runs == 2
