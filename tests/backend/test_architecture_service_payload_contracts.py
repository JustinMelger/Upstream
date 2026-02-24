from __future__ import annotations

import ast
from pathlib import Path

import pytest


pytestmark = pytest.mark.architecture
_SERVICES_ROOT = Path("backend/services")


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _service_methods(tree: ast.Module) -> dict[str, ast.AsyncFunctionDef]:
    methods: dict[str, ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not node.name.endswith("Service"):
            continue
        for item in node.body:
            if isinstance(item, ast.AsyncFunctionDef):
                methods[item.name] = item
    return methods


def _service_paths() -> list[Path]:
    return sorted(path for path in _SERVICES_ROOT.glob("*_service.py") if path.name != "ai_curator_service.py")


def _calls_parse_helper(node: ast.AsyncFunctionDef) -> bool:
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        func = inner.func
        if not isinstance(func, ast.Attribute):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "self"):
            continue
        if func.attr.startswith("_parse_"):
            return True
    return False


def _parse_helpers(tree: ast.Module) -> list[ast.FunctionDef]:
    helpers: list[ast.FunctionDef] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not node.name.endswith("Service"):
            continue
        for item in node.body:
            if not (isinstance(item, ast.FunctionDef) and item.name.startswith("_parse_")):
                continue
            arg_names = {arg.arg for arg in item.args.args}
            if "payload" not in arg_names:
                continue
            helpers.append(item)
    return helpers


def _excepts_validation_error(handler: ast.ExceptHandler) -> bool:
    if isinstance(handler.type, ast.Name):
        return handler.type.id == "ValidationError"
    if isinstance(handler.type, ast.Tuple):
        return any(isinstance(elt, ast.Name) and elt.id == "ValidationError" for elt in handler.type.elts)
    return False


def _has_invalid_payload_service_error_raise(node: ast.AST) -> bool:
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Raise):
            continue
        exc = inner.exc
        if not isinstance(exc, ast.Call):
            continue
        if not isinstance(exc.func, ast.Name) or not exc.func.id.endswith("ServiceError"):
            continue
        kwargs = {kw.arg: kw.value for kw in exc.keywords if kw.arg is not None}
        detail = kwargs.get("detail")
        status_code = kwargs.get("status_code")
        if not (
            isinstance(detail, ast.Constant)
            and detail.value == "invalid_payload"
            and isinstance(status_code, ast.Constant)
            and status_code.value == 400
        ):
            continue
        return True
    return False


def _parse_helper_maps_validation_error(node: ast.FunctionDef) -> bool:
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Try):
            continue
        for handler in inner.handlers:
            if _excepts_validation_error(handler) and _has_invalid_payload_service_error_raise(handler):
                return True
    return False


def test_service_entrypoints_use_typed_parse_helpers() -> None:
    """Guard the service boundary contract: entrypoints parse typed input first."""
    expected: dict[Path, set[str]] = {
        Path("backend/services/auth_service.py"): {
            "is_admin",
            "create_session",
            "get_session",
            "revoke_sessions",
            "get_user",
            "create_user",
            "update_password",
            "delete_user",
            "authenticate_user",
            "set_user_disabled",
        },
        Path("backend/services/courses_service.py"): {"create_course", "update_course"},
        Path("backend/services/paths_service.py"): {"create_path", "update_path"},
        Path("backend/services/articles_service.py"): {"create_article"},
        Path("backend/services/course_reviews_service.py"): {"create_review"},
        Path("backend/services/path_reviews_service.py"): {"create_review"},
        Path("backend/services/article_reviews_service.py"): {"create_review"},
        Path("backend/services/course_recommendations_service.py"): {"create_recommendation"},
        Path("backend/services/path_recommendations_service.py"): {"create_recommendation"},
        Path("backend/services/tracking_service.py"): {
            "list_tracking",
            "list_recent_activity",
            "upsert_tracking",
            "remove_tracking",
        },
        Path("backend/services/user_paths_service.py"): {
            "add_user_path",
            "list_user_paths",
            "remove_user_path",
            "update_user_path_status",
        },
        Path("backend/services/notifications_service.py"): {"list_activity"},
    }

    for path, required_methods in expected.items():
        tree = _parse(path)
        methods = _service_methods(tree)
        for method_name in required_methods:
            method = methods.get(method_name)
            assert method is not None, f"Missing expected service method {method_name} in {path}"
            assert _calls_parse_helper(method), f"Expected {path}:{method_name} to call self._parse_* helper"


def test_parse_helpers_map_validation_error_to_invalid_payload_domain_error() -> None:
    """Guard parse-helper error mapping consistency for service boundaries."""
    found_any_helper = False
    for path in _service_paths():
        tree = _parse(path)
        helpers = _parse_helpers(tree)
        if not helpers:
            continue
        found_any_helper = True
        for helper in helpers:
            assert _parse_helper_maps_validation_error(helper), (
                f"Expected {path}:{helper.name} to map ValidationError to "
                "*ServiceError(detail='invalid_payload', status_code=400)"
            )
    assert found_any_helper, "Expected at least one service payload parse helper in backend/services"
