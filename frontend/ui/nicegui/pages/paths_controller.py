"""Compatibility shim for Paths MVC module layout.

Deprecated import path:
    frontend.ui.nicegui.pages.paths_controller
Preferred import paths:
    frontend.ui.nicegui.pages.paths.controller
    frontend.ui.nicegui.pages.paths.state
"""

from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.state import PathDetailBundle, PathsPageState


__all__ = ["PathsPageController", "PathsPageState", "PathDetailBundle"]
