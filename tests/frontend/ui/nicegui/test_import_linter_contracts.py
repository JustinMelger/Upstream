from __future__ import annotations

import subprocess

import pytest


pytestmark = pytest.mark.architecture


def test_import_linter_contracts_are_kept() -> None:
    result = subprocess.run(
        ["lint-imports"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Import Linter contracts failed:\n{result.stdout}\n{result.stderr}"
