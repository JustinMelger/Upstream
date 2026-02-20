from __future__ import annotations

import ast
from pathlib import Path

import pytest


_LEARNING_DIR = Path("frontend/ui/nicegui/pages/learning")


def _imports_for(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(str(alias.name))
        elif isinstance(node, ast.ImportFrom):
            out.add(str(node.module or ""))
    return out


@pytest.mark.unit
def test_learning_pure_modules_do_not_import_nicegui() -> None:
    for filename in ["controller.py", "route_init.py", "state.py", "ui_glue.py", "view_model.py"]:
        imports = _imports_for(_LEARNING_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_learning_page_imports_controller_and_state() -> None:
    imports = _imports_for(_LEARNING_DIR / "page.py")
    assert "frontend.ui.nicegui.pages.learning.controller" in imports
    assert "frontend.ui.nicegui.pages.learning.actions" in imports
    assert "frontend.ui.nicegui.pages.learning.route_init" in imports
    assert "frontend.ui.nicegui.pages.learning.state" in imports
    assert "frontend.ui.nicegui.pages.learning.sections" in imports
    assert "frontend.ui.nicegui.pages.learning.ui_glue" in imports
    assert "frontend.ui.nicegui.pages.learning.view_model" in imports
    assert "frontend.ui.nicegui.services.learning_service" not in imports


@pytest.mark.unit
def test_learning_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"actions.py", "page.py", "sections.py"}
    for path in sorted(_LEARNING_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui
