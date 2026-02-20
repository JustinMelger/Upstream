from __future__ import annotations

from pathlib import Path


def test_pages_use_package_layout_only() -> None:
    pages_root = Path("frontend/ui/nicegui/pages")
    top_level_py = sorted(p.name for p in pages_root.glob("*.py"))
    assert top_level_py == ["__init__.py"]


def test_each_page_package_has_init_and_page_module() -> None:
    pages_root = Path("frontend/ui/nicegui/pages")
    package_dirs = sorted(p for p in pages_root.iterdir() if p.is_dir() and not p.name.startswith("__"))
    assert package_dirs, "Expected at least one page package directory"
    for pkg in package_dirs:
        assert (pkg / "__init__.py").exists(), f"Missing __init__.py in {pkg}"
        assert (pkg / "page.py").exists(), f"Missing page.py in {pkg}"
