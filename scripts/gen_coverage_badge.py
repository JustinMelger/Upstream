from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def _color_for(percentage: int) -> str:
    if percentage >= 90:
        return "#4c1"  # brightgreen
    if percentage >= 80:
        return "#97CA00"  # green
    if percentage >= 70:
        return "#a4a61d"  # yellowgreen-ish
    if percentage >= 60:
        return "#dfb317"  # yellow
    return "#e05d44"  # red


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def render_badge(*, label: str, value: str, color: str) -> str:
    label = _escape(label)
    value = _escape(value)

    # A tiny shields-style SVG. Width is approximate but good enough for GitHub rendering.
    label_w = max(50, 8 * len(label) + 20)
    value_w = max(40, 8 * len(value) + 20)
    total_w = label_w + value_w
    label_x = label_w / 2
    value_x = label_w + value_w / 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}: {value}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_w}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="20" fill="#555"/>
    <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_x}" y="14">{label}</text>
    <text x="{value_x}" y="14">{value}</text>
  </g>
</svg>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: gen_coverage_badge.py <coverage.xml> <output.svg>", file=sys.stderr)
        return 2

    coverage_xml = Path(argv[1])
    output_svg = Path(argv[2])

    root = ET.parse(coverage_xml).getroot()
    line_rate = root.attrib.get("line-rate")
    if not line_rate:
        percentage = 0
    else:
        percentage = int(round(float(line_rate) * 100))

    svg = render_badge(label="coverage", value=f"{percentage}%", color=_color_for(percentage))
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    output_svg.write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
