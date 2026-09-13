"""Export approved technical covers to responsive WebP files and review sheets."""

import argparse
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
ARTWORK = ROOT / "frontend/react/public/artwork"
RECORDS = Path(__file__).parent


def main():
    """Resize generated sources to the existing image sizes and byte budgets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing the original generated PNG files named in the manifest.",
    )
    args = parser.parse_args()
    records = json.loads((RECORDS / "generation-record.json").read_text())
    expected = {f"{kind}-{i}" for kind in ("article", "video", "course", "path") for i in range(10)}
    if {row["key"] for row in records} != expected:
        raise ValueError(f"Incomplete collection: {len(records)}/40 sources")
    for row in records:
        source = Image.open(args.source_dir / row["source"]).convert("RGB")
        for suffix, size, budget in [
            ("", (1280, 720), 200_000),
            ("-card", (640, 360), 60_000),
        ]:
            target = ARTWORK / f"{row['key']}{suffix}.webp"
            resized = source.resize(size, Image.Resampling.LANCZOS)
            for quality in range(88, 17, -5):
                resized.save(target, "WEBP", quality=quality, method=6)
                if target.stat().st_size <= budget:
                    break
            else:
                raise ValueError(f"Image exceeds budget: {target}")
        row["asset"] = f"frontend/react/public/artwork/{row['key']}.webp"
        if row["key"].endswith("-0"):
            for suffix in ("", "-card"):
                shutil.copyfile(
                    ARTWORK / f"{row['key']}{suffix}.webp",
                    ARTWORK / f"{row['type']}-technical{suffix}.webp",
                )
    (RECORDS / "generation-record.json").write_text(json.dumps(records, indent=2) + "\n")
    for kind in ("article", "video", "course", "path"):
        sheet = Image.new("RGB", (664, 1056), "#1c2935")
        draw = ImageDraw.Draw(sheet)
        for i in range(10):
            x, y = 8 + (i % 2) * 328, 12 + (i // 2) * 208
            cover = Image.open(ARTWORK / f"{kind}-{i}-card.webp")
            sheet.paste(cover.resize((320, 180), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 8, y + 185), f"{kind}-{i}", fill="#b9c7d8")
        sheet.save(RECORDS / f"{kind}-collection.webp", "WEBP", quality=90, method=6)
    total = sum((ARTWORK / f"{key}{suffix}.webp").stat().st_size for key in expected for suffix in ("", "-card"))
    print(f"Exported 40 covers, 80 responsive assets: {total:,} bytes")  # noqa: T201


if __name__ == "__main__":
    main()
