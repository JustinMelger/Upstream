"""NiceGUI entrypoint.

Run with:
    `uv run python -m frontend.ui.nicegui`
"""


def main() -> None:
    """Dispatch to the canonical entrypoint in `frontend.ui.nicegui.main`."""
    from frontend.ui.nicegui.main import main as _main

    _main()


if __name__ in {"__main__", "__mp_main__"}:
    main()
