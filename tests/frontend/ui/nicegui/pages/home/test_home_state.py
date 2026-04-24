from frontend.ui.nicegui.pages.shared_stats.state import SharedStatsState


def test_home_state_defaults_pending_reload_false() -> None:
    state = SharedStatsState()
    assert state.pending_reload is False
