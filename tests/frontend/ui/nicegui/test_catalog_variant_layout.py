from __future__ import annotations

import ast
from pathlib import Path


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imports_for(path: Path) -> set[str]:
    tree = _parse(path)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(str(alias.name))
        elif isinstance(node, ast.ImportFrom):
            out.add(str(node.module or ""))
    return out


def _calls_function_named(path: Path, name: str) -> bool:
    tree = _parse(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == name:
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == name:
            return True
    return False


def test_catalog_pages_use_variant_scope_layout() -> None:
    pages = [
        Path("frontend/ui/nicegui/pages/courses/page.py"),
        Path("frontend/ui/nicegui/pages/articles/page.py"),
        Path("frontend/ui/nicegui/pages/paths/page.py"),
        Path("frontend/ui/nicegui/pages/explore/page.py"),
    ]
    for page in pages:
        imports = _imports_for(page)
        assert "frontend.ui.nicegui.components.layout" in imports
        assert _calls_function_named(page, "render_catalog_scope"), f"Expected render_catalog_scope call in {page}"
