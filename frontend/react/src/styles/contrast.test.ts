import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const css = readFileSync("src/styles/global.css", "utf8");
const colors = Object.fromEntries(
  [...css.matchAll(/--([a-z-]+):\s*(#[a-fA-F0-9]{6});/g)].map((match) => [
    match[1],
    match[2],
  ]),
);

function luminance(hex: string) {
  const channels = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));

  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function contrast(a: string, b: string) {
  const [low, high] = [luminance(colors[a]), luminance(colors[b])].sort(
    (a, b) => a - b,
  );

  return (high + 0.05) / (low + 0.05);
}

describe("semantic palette contrast", () => {
  it("keeps text and content accents readable on neutral surfaces", () => {
    for (const text of [
      "text",
      "muted",
      "accent",
      "article",
      "video",
      "path",
      "success",
      "danger",
    ])
      for (const surface of ["bg", "surface", "raised"])
        expect(contrast(text, surface)).toBeGreaterThanOrEqual(4.5);
    expect(contrast("on-accent", "accent")).toBeGreaterThanOrEqual(4.5);
  });
  it("distinguishes control boundaries and focus indicators", () => {
    for (const surface of ["bg", "surface"])
      expect(contrast("control", surface)).toBeGreaterThanOrEqual(3);
    for (const surface of ["bg", "surface", "raised", "selected"])
      expect(contrast("accent", surface)).toBeGreaterThanOrEqual(3);
  });
});
