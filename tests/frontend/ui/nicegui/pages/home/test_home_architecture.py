from __future__ import annotations

import ast
from pathlib import Path

import pytest


_HOME_DIR = Path("frontend/ui/nicegui/pages/home")


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
def test_home_pure_modules_do_not_import_nicegui() -> None:
    for filename in ["controller.py", "state.py", "transitions.py", "helpers.py"]:
        imports = _imports_for(_HOME_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_home_page_redirect_module_stays_decoupled_from_home_page_stack() -> None:
    imports = _imports_for(_HOME_DIR / "page.py")
    assert "nicegui" in imports
    assert "frontend.ui.nicegui.core.api_client" in imports
    assert "frontend.ui.nicegui.core.session_store" in imports
    assert "frontend.ui.nicegui.pages.home.controller" not in imports
    assert "frontend.ui.nicegui.pages.home.sections" not in imports
    assert "frontend.ui.nicegui.pages.home.state" not in imports
    assert "frontend.ui.nicegui.pages.home.transitions" not in imports


@pytest.mark.unit
def test_home_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"page.py", "sections.py"}
    for path in sorted(_HOME_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui
