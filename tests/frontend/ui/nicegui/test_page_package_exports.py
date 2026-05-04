from __future__ import annotations

import importlib
from pathlib import Path


def test_page_packages_export_register_only() -> None:
    pages_root = Path("frontend/ui/nicegui/pages")
    package_dirs = sorted(p for p in pages_root.iterdir() if p.is_dir() and (p / "__init__.py").exists())
    package_without_register = {"shared_activity", "shared_stats"}
    for pkg in package_dirs:
        mod = importlib.import_module(f"frontend.ui.nicegui.pages.{pkg.name}")
        exported = list(getattr(mod, "__all__", []))
        if pkg.name in package_without_register:
            assert exported == [], f"{pkg.name} exports unexpected symbols: {exported}"
        else:
            assert exported == ["register"], f"{pkg.name} exports unexpected symbols: {exported}"
