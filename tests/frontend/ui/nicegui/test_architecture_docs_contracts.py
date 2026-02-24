from __future__ import annotations

import ast
from pathlib import Path

import pytest


pytestmark = pytest.mark.architecture

_PAGES_ROOT = Path("frontend/ui/nicegui/pages")
_MAIN_FILE = Path("frontend/ui/nicegui/main.py")


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


def _decorated_routes(path: Path) -> set[str]:
    tree = _parse(path)
    routes: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr != "page":
                continue
            if not isinstance(decorator.func.value, ast.Name) or decorator.func.value.id != "ui":
                continue
            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                routes.add(decorator.args[0].value)
    return routes


def _has_require_user_call(path: Path) -> bool:
    tree = _parse(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "require_user":
            return True
    return False


def _admin_page_requires_admin(path: Path) -> bool:
    tree = _parse(path)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "require_user"):
            continue
        for keyword in node.keywords:
            if keyword.arg == "require_admin" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                return True
    return False


def test_documented_routes_exist_in_page_modules() -> None:
    documented_routes = {
        "/",
        "/login",
        "/home",
        "/learning",
        "/teams",
        "/activity",
        "/profile",
        "/profile/stats",
        "/courses",
        "/paths",
        "/articles",
        "/insights",
        "/admin/users",
        "/ai",
    }
    declared_routes: set[str] = set()
    for page_file in sorted(_PAGES_ROOT.glob("*/page.py")):
        declared_routes |= _decorated_routes(page_file)
    for route in documented_routes:
        assert route in declared_routes, f"Missing documented route: {route}"


def test_non_login_pages_require_auth_guard() -> None:
    for page_file in sorted(_PAGES_ROOT.glob("*/page.py")):
        if page_file.parent.name == "login":
            continue
        assert _has_require_user_call(page_file), f"Expected require_user guard in {page_file}"


def test_admin_users_page_requires_admin_guard() -> None:
    admin_page = _PAGES_ROOT / "admin_users" / "page.py"
    assert _admin_page_requires_admin(admin_page), "Expected require_user(..., require_admin=True)"


def test_main_create_app_keeps_feature_flag_gates() -> None:
    source = _MAIN_FILE.read_text(encoding="utf-8")
    assert "if settings.feature_ai_curator:" in source
    assert "ai_curator.register(store=store, api=api)" in source
    assert "if settings.feature_articles:" in source
    assert "articles.register(store=store, api=api)" in source


def test_pages_and_services_do_not_import_httpx_directly() -> None:
    roots = [
        Path("frontend/ui/nicegui/pages"),
        Path("frontend/ui/nicegui/services"),
    ]
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            imports = _imports_for(path)
            assert "httpx" not in imports
            assert not any(name.startswith("httpx.") for name in imports)


def test_page_modules_do_not_import_services_directly() -> None:
    for path in sorted(_PAGES_ROOT.glob("*/page.py")):
        imports = _imports_for(path)
        assert not any(name.startswith("frontend.ui.nicegui.services") for name in imports), (
            f"page.py should use controller/actions, not services directly: {path}"
        )


def test_page_modules_do_not_call_api_client_methods_directly() -> None:
    for path in sorted(_PAGES_ROOT.glob("*/page.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"get", "post", "put", "delete"}:
                continue
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "api":
                raise AssertionError(f"page.py should route API calls through controller/services: {path}")


def test_ui_flow_modules_do_not_call_api_client_methods_directly() -> None:
    for pattern in ("*/dialogs.py", "*/detail_flow.py"):
        for path in sorted(_PAGES_ROOT.glob(pattern)):
            tree = _parse(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"get", "post", "put", "delete"}:
                    continue
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "api":
                    raise AssertionError(f"UI flow module should route API calls through controller/service callbacks: {path}")


def test_controller_modules_do_not_import_nicegui_ui_primitives() -> None:
    for path in sorted(_PAGES_ROOT.glob("*/controller.py")):
        imports = _imports_for(path)
        assert "nicegui" not in imports, f"controller should not import nicegui directly: {path}"
        assert "nicegui.ui" not in imports, f"controller should not import nicegui.ui: {path}"
        assert "nicegui.app" not in imports, f"controller should not import nicegui.app: {path}"


def test_page_package_modules_do_not_use_broad_exception_handlers() -> None:
    for path in sorted(_PAGES_ROOT.rglob("*.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:
                raise AssertionError(f"Broad bare except is not allowed in page modules: {path}")
            if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                raise AssertionError(f"Broad except Exception is not allowed in page modules: {path}")


def test_card_pages_use_view_model_mappers() -> None:
    """Guard view-model boundary: page modules should call page-local view-model mappers."""
    expected: dict[Path, tuple[str, tuple[str, ...]]] = {
        Path("frontend/ui/nicegui/pages/courses/page.py"): (
            "frontend.ui.nicegui.pages.courses.view_model",
            ("map_course_card_view",),
        ),
        Path("frontend/ui/nicegui/pages/paths/page.py"): (
            "frontend.ui.nicegui.pages.paths.view_model",
            ("map_path_card_view",),
        ),
        Path("frontend/ui/nicegui/pages/articles/page.py"): (
            "frontend.ui.nicegui.pages.articles.view_model",
            ("map_article_card_view",),
        ),
        Path("frontend/ui/nicegui/pages/learning/page.py"): (
            "frontend.ui.nicegui.pages.learning.view_model",
            ("build_learning_tab_view", "build_shared_tab_view"),
        ),
    }
    for page_path, (module_name, mapper_names) in expected.items():
        imports = _imports_for(page_path)
        assert module_name in imports, f"Expected {page_path} to import {module_name}"
        for mapper_name in mapper_names:
            assert _calls_function_named(page_path, mapper_name), f"Expected {page_path} to call {mapper_name}"


def test_large_page_modules_stay_below_size_guardrail() -> None:
    """Keep large page modules from regressing while migration continues."""
    max_lines = 550
    guarded_pages = [
        Path("frontend/ui/nicegui/pages/courses/page.py"),
        Path("frontend/ui/nicegui/pages/paths/page.py"),
        Path("frontend/ui/nicegui/pages/articles/page.py"),
        Path("frontend/ui/nicegui/pages/learning/page.py"),
    ]
    for page_path in guarded_pages:
        line_count = len(page_path.read_text(encoding="utf-8").splitlines())
        assert line_count <= max_lines, f"{page_path} is {line_count} lines (> {max_lines}); extract to package modules"
