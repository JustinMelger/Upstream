from __future__ import annotations

import ast
from pathlib import Path

import pytest


_ADMIN_USERS_DIR = Path("frontend/ui/nicegui/pages/admin_users")


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
def test_admin_users_pure_modules_do_not_import_nicegui() -> None:
    for filename in ["controller.py", "state.py", "transitions.py", "ui_glue.py"]:
        imports = _imports_for(_ADMIN_USERS_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_admin_users_page_imports_admin_users_domain_modules() -> None:
    imports = _imports_for(_ADMIN_USERS_DIR / "page.py")
    assert "frontend.ui.nicegui.pages.admin_users.controller" in imports
    assert "frontend.ui.nicegui.pages.admin_users.sections" in imports
    assert "frontend.ui.nicegui.pages.admin_users.state" in imports
    assert "frontend.ui.nicegui.pages.admin_users.transitions" in imports
    assert "frontend.ui.nicegui.pages.admin_users.ui_glue" in imports


@pytest.mark.unit
def test_admin_users_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"page.py"}
    for path in sorted(_ADMIN_USERS_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui
