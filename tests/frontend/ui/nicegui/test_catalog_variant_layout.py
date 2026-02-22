from __future__ import annotations

import ast
from pathlib import Path

import pytest


pytestmark = pytest.mark.architecture


_THEME_FILE = Path("frontend/ui/nicegui/core/theme.py")

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


def _calls_render_catalog_scope_with_variant(path: Path, *, variant: str) -> bool:
    tree = _parse(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "render_catalog_scope":
            continue
        for keyword in node.keywords:
            if keyword.arg != "variant":
                continue
            if isinstance(keyword.value, ast.Constant) and str(keyword.value.value) == str(variant):
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


def test_catalog_pages_use_expected_scope_variants() -> None:
    expected = {
        Path("frontend/ui/nicegui/pages/courses/page.py"): "courses",
        Path("frontend/ui/nicegui/pages/articles/page.py"): "articles",
        Path("frontend/ui/nicegui/pages/paths/page.py"): "paths",
        Path("frontend/ui/nicegui/pages/explore/page.py"): "explore",
    }
    for page, variant in expected.items():
        assert _calls_render_catalog_scope_with_variant(page, variant=variant), (
            f"Expected {page} to call render_catalog_scope(variant='{variant}')"
        )


def test_catalog_identity_hero_used_on_primary_catalog_pages() -> None:
    for page in [
        Path("frontend/ui/nicegui/pages/courses/page.py"),
        Path("frontend/ui/nicegui/pages/articles/page.py"),
        Path("frontend/ui/nicegui/pages/paths/page.py"),
    ]:
        imports = _imports_for(page)
        assert "frontend.ui.nicegui.components.catalog_hero" in imports
        assert _calls_function_named(page, "render_catalog_hero"), f"Expected render_catalog_hero call in {page}"


def test_catalog_variant_css_selectors_are_defined_in_theme() -> None:
    theme_src = _THEME_FILE.read_text(encoding="utf-8")
    for selector in [
        ".lp-catalog-scope",
        ".lp-catalog-scope.lp-catalog--courses",
        ".lp-catalog-scope.lp-catalog--articles",
        ".lp-catalog-scope.lp-catalog--paths",
        ".lp-catalog-scope.lp-catalog--explore",
    ]:
        assert selector in theme_src


def test_page_modules_do_not_define_catalog_variant_classnames_directly() -> None:
    for page in sorted(Path("frontend/ui/nicegui/pages").glob("*/page.py")):
        src = page.read_text(encoding="utf-8")
        assert "lp-catalog--" not in src, f"Variant classname should be assigned via render_catalog_scope only: {page}"
