from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageChops
from playwright.async_api import Page


def _visual_assert_enabled() -> bool:
    return str(os.getenv("E2E_VISUAL_ASSERT", "1")).strip() not in {"0", "false", "False"}


def _strict_mode() -> bool:
    return str(os.getenv("E2E_VISUAL_STRICT", "0")).strip() in {"1", "true", "True"}


def _update_baselines_mode() -> bool:
    return str(os.getenv("E2E_UPDATE_VISUAL_BASELINES", "0")).strip() in {"1", "true", "True"}


def _max_diff_pixels() -> int:
    raw = str(os.getenv("E2E_VISUAL_MAX_DIFF_PIXELS", "300")).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 300


def _baseline_dir() -> Path:
    root = Path(os.getenv("E2E_VISUAL_BASELINE_DIR", "tests/e2e/baselines"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _artifacts_dir() -> Path:
    root = Path(os.getenv("E2E_SCREENSHOT_DIR", "tests/e2e/artifacts"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_visual_note(*, name: str, message: str) -> None:
    """Persist non-strict visual warnings as CI-reviewable artifacts."""
    note_path = _artifacts_dir() / f"note_{Path(name).stem}.txt"
    note_path.write_text(f"{message}\n", encoding="utf-8")


async def assert_visual_snapshot(*, page: Page, name: str, full_page: bool = True) -> None:
    """Compare current page screenshot against a baseline image."""
    if not _visual_assert_enabled():
        return

    baseline_path = _baseline_dir() / str(name)
    artifacts_path = _artifacts_dir()
    actual_path = artifacts_path / f"actual_{name}"
    diff_path = artifacts_path / f"diff_{name}"

    screenshot = await page.screenshot(path=str(actual_path), full_page=bool(full_page))
    current_img = Image.open(actual_path).convert("RGBA")

    if _update_baselines_mode():
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(screenshot)
        return

    if not baseline_path.exists():
        message = f"Visual baseline missing: {baseline_path}."
        if _strict_mode():
            raise AssertionError(f"{message} Run with E2E_UPDATE_VISUAL_BASELINES=1 to create/refresh baselines.")
        _write_visual_note(name=name, message=message)
        return

    baseline_img = Image.open(baseline_path).convert("RGBA")
    if baseline_img.size != current_img.size:
        message = f"Visual snapshot size mismatch for {name}: baseline={baseline_img.size}, current={current_img.size}"
        if _strict_mode():
            raise AssertionError(message)
        _write_visual_note(name=name, message=message)
        return

    diff = ImageChops.difference(baseline_img, current_img)
    bbox = diff.getbbox()
    if bbox is None:
        return

    non_zero = sum(1 for px in diff.getdata() if px != (0, 0, 0, 0))
    allowed = _max_diff_pixels()
    if non_zero <= allowed:
        return

    diff.save(diff_path)
    raise AssertionError(
        f"Visual regression for {name}: {non_zero} diff pixels exceeds allowed {allowed}. See {actual_path} and {diff_path}."
    )
