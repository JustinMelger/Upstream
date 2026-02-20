from frontend.ui.nicegui.pages.home.state import HomePageState


def test_home_state_defaults_pending_reload_false() -> None:
    state = HomePageState()
    assert state.pending_reload is False
