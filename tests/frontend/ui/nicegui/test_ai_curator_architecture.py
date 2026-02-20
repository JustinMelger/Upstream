from __future__ import annotations

import ast
from pathlib import Path

import pytest


_AI_CURATOR_DIR = Path("frontend/ui/nicegui/pages/ai_curator")


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
def test_ai_curator_pure_modules_do_not_import_nicegui() -> None:
    for filename in ["controller.py", "state.py", "transitions.py", "ui_glue.py"]:
        imports = _imports_for(_AI_CURATOR_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_ai_curator_page_imports_ai_curator_domain_modules() -> None:
    imports = _imports_for(_AI_CURATOR_DIR / "page.py")
    assert "frontend.ui.nicegui.pages.ai_curator.controller" in imports
    assert "frontend.ui.nicegui.pages.ai_curator.state" in imports
    assert "frontend.ui.nicegui.pages.ai_curator.transitions" in imports


@pytest.mark.unit
def test_ai_curator_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"page.py"}
    for path in sorted(_AI_CURATOR_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui
