from __future__ import annotations

import ast
from pathlib import Path

import pytest


_EXPLORE_DIR = Path("frontend/ui/nicegui/pages/explore")


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
def test_explore_pure_modules_do_not_import_nicegui() -> None:
    for filename in [
        "controller.py",
        "orchestration.py",
        "state.py",
        "ui_glue.py",
    ]:
        imports = _imports_for(_EXPLORE_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_explore_page_imports_page_package_modules() -> None:
    imports = _imports_for(_EXPLORE_DIR / "page.py")
    assert "frontend.ui.nicegui.pages.explore.controller" in imports
    assert "frontend.ui.nicegui.pages.explore.detail_flow" in imports
    assert "frontend.ui.nicegui.pages.explore.list_sections" in imports
    assert "frontend.ui.nicegui.pages.explore.sections" in imports
    assert "frontend.ui.nicegui.pages.explore.state" in imports
    assert "frontend.ui.nicegui.pages.explore.ui_glue" in imports
    assert "frontend.ui.nicegui.services.courses_service" not in imports
    assert "frontend.ui.nicegui.services.articles_service" not in imports


@pytest.mark.unit
def test_explore_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    expected_ui_modules = {"actions.py", "page.py", "sections.py", "detail_flow.py", "list_sections.py"}
    for path in sorted(_EXPLORE_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if path.name in expected_ui_modules:
            assert imports_nicegui
        else:
            assert not imports_nicegui


@pytest.mark.unit
def test_explore_article_cards_use_compact_mode() -> None:
    src = (_EXPLORE_DIR / "list_sections.py").read_text(encoding="utf-8")
    assert "render_article_card(" in src
    assert "compact_mode=True" in src
