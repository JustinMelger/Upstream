from __future__ import annotations

import ast
from pathlib import Path
import re
import tomllib

import pytest


pytestmark = pytest.mark.architecture

_PAGES_ROOT = Path("frontend/ui/nicegui/pages")
_SERVICES_ROOT = Path("frontend/ui/nicegui/services")
_MAIN_FILE = Path("frontend/ui/nicegui/main.py")
_PYPROJECT_FILE = Path("pyproject.toml")


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
        "/teams",
        "/profile",
        "/profile/stats",
        "/explore",
        "/explore/courses/{course_id}",
        "/explore/videos/{video_id}",
        "/explore/paths/{path_id}",
        "/explore/articles/{article_id}",
        "/share/item",
        "/share/path",
        "/admin/users",
        "/ai",
    }
    declared_routes: set[str] = set()
    for page_file in sorted(_PAGES_ROOT.glob("*/page.py")):
        declared_routes |= _decorated_routes(page_file)
    for route in documented_routes:
        assert route in declared_routes, f"Missing documented route: {route}"


def test_share_route_contract_includes_compatibility_routes() -> None:
    share_page = _PAGES_ROOT / "share" / "page.py"
    declared_routes = _decorated_routes(share_page)
    assert "/share/item" in declared_routes
    assert "/share/path" in declared_routes
    assert "/share/course" in declared_routes
    assert "/share/article" in declared_routes


def test_non_login_pages_require_auth_guard() -> None:
    for page_file in sorted(_PAGES_ROOT.glob("*/page.py")):
        if page_file.parent.name == "login":
            continue
        assert _has_require_user_call(page_file), f"Expected require_user guard in {page_file}"


def test_admin_users_page_requires_admin_guard() -> None:
    admin_page = _PAGES_ROOT / "admin_users" / "page.py"
    assert _admin_page_requires_admin(admin_page), "Expected require_user(..., require_admin=True)"


def test_legacy_catalog_compat_modules_are_removed() -> None:
    removed = (
        Path("frontend/ui/nicegui/pages/courses/compat.py"),
        Path("frontend/ui/nicegui/pages/paths/compat.py"),
        Path("frontend/ui/nicegui/pages/articles/compat.py"),
    )
    for path in removed:
        assert not path.exists(), f"Legacy compatibility module should be removed: {path}"


def test_page_modules_do_not_navigate_to_legacy_discovery_routes() -> None:
    forbidden = {
        "/courses",
        "/paths",
        "/articles",
        "/manage/courses",
        "/manage/paths",
        "/manage/articles",
        "/learning",
        "/activity",
        "/insights",
    }
    for page_path in sorted(_PAGES_ROOT.glob("*/page.py")):
        tree = _parse(page_path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "to"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "navigate"
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "ui"
            ):
                continue
            if not node.args:
                continue
            first = node.args[0]
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            value = str(first.value)
            if value in forbidden or any(value.startswith(f"{route}?") for route in forbidden):
                raise AssertionError(f"Use Explore routes instead of legacy discovery route in {page_path}: {value}")


def test_main_create_app_keeps_feature_flag_gates() -> None:
    source = _MAIN_FILE.read_text(encoding="utf-8")
    assert "if settings.feature_ai_curator:" in source
    assert "ai_curator.register(store=store, api=api)" in source
    assert "courses.register(store=store, api=api)" not in source
    assert "paths.register(store=store, api=api)" not in source
    assert "articles.register(store=store, api=api)" not in source


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


def test_service_modules_do_not_import_pages_modules() -> None:
    for path in sorted(_SERVICES_ROOT.rglob("*.py")):
        imports = _imports_for(path)
        assert not any(name.startswith("frontend.ui.nicegui.pages") for name in imports), (
            f"service module should not depend on page modules: {path}"
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
    max_lines_by_page = {
        Path("frontend/ui/nicegui/pages/learning/page.py"): 353,
        Path("frontend/ui/nicegui/pages/explore/page.py"): 280,
    }
    for page_path, max_lines in max_lines_by_page.items():
        line_count = len(page_path.read_text(encoding="utf-8").splitlines())
        assert line_count <= max_lines, f"{page_path} is {line_count} lines (> {max_lines}); extract to package modules"


def test_active_page_modules_do_not_add_complexity_noqa_markers() -> None:
    """Guardrail: avoid adding local complexity suppressions in active page modules."""
    complexity_noqa = re.compile(r"#\s*noqa:\s*.*\b(C901|PLR0911|PLR0912|PLR0913|PLR0915)\b")
    active_module_patterns = (
        "*/page.py",
        "*/controller.py",
        "*/orchestration.py",
        "*/actions.py",
        "*/ui_glue.py",
    )
    for pattern in active_module_patterns:
        for path in sorted(_PAGES_ROOT.glob(pattern)):
            src = path.read_text(encoding="utf-8")
            if complexity_noqa.search(src):
                raise AssertionError(f"Do not add complexity noqa markers in active page modules: {path}")


def test_ruff_complexity_per_file_ignores_do_not_broaden_scope() -> None:
    """Guardrail: keep complexity ignores constrained to approved module scopes."""
    pyproject = tomllib.loads(_PYPROJECT_FILE.read_text(encoding="utf-8"))
    per_file_ignores: dict[str, list[str]] = (
        pyproject.get("tool", {}).get("ruff", {}).get("lint", {}).get("per-file-ignores", {})
    )
    complexity_codes = {"C901", "PLR0911", "PLR0912", "PLR0913", "PLR0915"}
    complexity_ignore_targets = {
        path
        for path, codes in dict(per_file_ignores or {}).items()
        if any(str(code) in complexity_codes for code in list(codes or []))
    }

    approved_targets = {
        "tests/**/*.py",
        "frontend/ui/nicegui/pages/admin_users/page.py",
        "frontend/ui/nicegui/pages/ai_curator/page.py",
        "frontend/ui/nicegui/pages/learning/page.py",
        "frontend/ui/nicegui/pages/profile/page.py",
        "frontend/ui/nicegui/pages/courses/sections.py",
        "frontend/ui/nicegui/pages/learning/sections.py",
    }
    unexpected = sorted(complexity_ignore_targets - approved_targets)
    assert not unexpected, (
        f"Unexpected Ruff complexity ignore targets. Refactor modules instead of broadening per-file ignores: {unexpected}"
    )
