from __future__ import annotations

import ast
from pathlib import Path

import pytest


_ACTIVITY_DIR = Path("frontend/ui/nicegui/pages/activity")


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
def test_activity_pure_modules_do_not_import_nicegui() -> None:
    for filename in ["controller.py", "state.py", "route_init.py", "transitions.py", "ui_glue.py", "view_model.py"]:
        imports = _imports_for(_ACTIVITY_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_activity_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"sections.py"}
    for path in sorted(_ACTIVITY_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui
