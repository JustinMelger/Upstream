from __future__ import annotations

from io import BytesIO

from PIL import Image
import pytest

from tests.e2e import visual_assertions


class _FakePage:
    def __init__(self, *, size: tuple[int, int]) -> None:
        self._size = size

    async def screenshot(self, *, path: str, full_page: bool) -> bytes:  # noqa: ARG002
        image = Image.new("RGBA", self._size, (20, 30, 40, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        data = buffer.getvalue()
        with open(path, "wb") as handle:
            handle.write(data)
        return data


@pytest.mark.anyio
async def test_visual_snapshot_writes_note_when_baseline_missing_in_non_strict_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("E2E_VISUAL_ASSERT", "1")
    monkeypatch.setenv("E2E_VISUAL_STRICT", "0")
    monkeypatch.setenv("E2E_VISUAL_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.setenv("E2E_SCREENSHOT_DIR", str(tmp_path / "artifacts"))

    await visual_assertions.assert_visual_snapshot(
        page=_FakePage(size=(10, 10)),
        name="home_after_login.png",
        full_page=False,
    )

    note = (tmp_path / "artifacts" / "note_home_after_login.txt").read_text(encoding="utf-8")
    assert "Visual baseline missing:" in note


@pytest.mark.anyio
async def test_visual_snapshot_writes_note_when_baseline_size_mismatches_in_non_strict_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (8, 8), (20, 30, 40, 255)).save(baseline_dir / "home_after_login.png")

    monkeypatch.setenv("E2E_VISUAL_ASSERT", "1")
    monkeypatch.setenv("E2E_VISUAL_STRICT", "0")
    monkeypatch.setenv("E2E_VISUAL_BASELINE_DIR", str(baseline_dir))
    monkeypatch.setenv("E2E_SCREENSHOT_DIR", str(tmp_path / "artifacts"))

    await visual_assertions.assert_visual_snapshot(
        page=_FakePage(size=(10, 10)),
        name="home_after_login.png",
        full_page=False,
    )

    note = (tmp_path / "artifacts" / "note_home_after_login.txt").read_text(encoding="utf-8")
    assert "Visual snapshot size mismatch" in note
