import { statSync } from "node:fs";

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { artworkKey, ResourceArtwork, ResourceCard } from "./resources";
import { Pagination } from "./ui";

describe("resource presentation", () => {
  it("preserves established variant assignments in the replacement library", () => {
    expect(artworkKey("course", "Production-ready Python")).toBe("course-0");
    expect(artworkKey("course", "  PRODUCTION-READY   PYTHON ")).toBe(
      "course-0",
    );
  });
  it("uses consistent artwork for normalized titles across all forty bounded assets", () => {
    expect(artworkKey("course", "  Useful   Learning ")).toBe(
      artworkKey("course", "useful learning"),
    );

    for (const type of ["course", "article", "video", "path"] as const) {
      const variants = new Set(
        Array.from({ length: 400 }, (_, i) =>
          artworkKey(type, `Resource ${i}`),
        ),
      );
      expect(variants.size).toBe(10);

      for (const key of variants) {
        expect(statSync(`public/artwork/${key}.webp`).size).toBeLessThanOrEqual(
          200000,
        );
        expect(
          statSync(`public/artwork/${key}-card.webp`).size,
        ).toBeLessThanOrEqual(60000);
      }
    }
  });
  it("falls back locally on failed artwork and retries a different resource", () => {
    const { container, rerender } = render(
      <ResourceArtwork type="article" title="A useful article" />,
    );
    fireEvent.error(container.querySelector("img")!);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("A useful article")).toBeTruthy();
    rerender(<ResourceArtwork type="article" title="Another useful article" />);
    expect(container.querySelector("img")).not.toBeNull();
  });
  it("has one resource link and separates author recommendations from ratings", () => {
    render(
      <MemoryRouter>
        <ResourceCard
          item={{
            id: 1,
            type: "article",
            title: "Clear feedback",
            description: "Useful skills",
            recommendation_note: "Helped me listen",
            created_by: "maya",
            rating: 4.5,
            review_count: 2,
          }}
        />
      </MemoryRouter>,
    );
    expect(screen.getAllByRole("link")).toHaveLength(1);
    expect(screen.getByText("Shared by maya")).toBeTruthy();
    expect(screen.getByText(/Helped me listen/)).toBeTruthy();
    expect(screen.getByText(/4.5 · 2 reviews/)).toBeTruthy();
  });
  it("does not repeat matching summary and note or invent reviews in previews", () => {
    render(
      <MemoryRouter>
        <ResourceCard
          preview
          item={{
            type: "article",
            title: "Draft",
            description: "My takeaway",
            recommendation_note: "My takeaway",
          }}
        />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("My takeaway")).toHaveLength(1);
    expect(screen.queryByText(/reviews/)).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });
  it("uses singular counts without inactive single-page controls", () => {
    render(<Pagination page={1} total={1} onChange={() => {}} />);
    expect(screen.getByText("1 result")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
