# Metadata and artwork decisions

Historical summary. Current instructions: [backend architecture](../architecture_backend.md#metadata-and-schema-compatibility), [artwork](../artwork/README.md) and [branding](../branding/README.md).

## Metadata — catalogued 2026-09-11

The metadata autofill record introduced explicit Fetch details on new course/article/video forms, preserving untouched-field rules, manual entry and draft recovery. Page-authored metadata was chosen over inferred classification or generated summaries. The fetcher uses public-destination validation and address pinning, redirect checks and bounded network/cache behaviour. Content reads do not initiate these requests.

The 2026-09-11 cleanup removed the separate external-cover fetcher and the obsolete metadata-autofill setting. Empty image/classification compatibility fields and explicit metadata fetching remained. This simplified reads without changing existing content contracts.

Migration `20260909_0018` added recommendation notes and nullable path creation dates; `20260909_0019` added article descriptions. Undated paths were not assigned invented share dates. These are historical migration identifiers, not instructions to rerun or edit migrations.

## Artwork refinement

The collection expanded to ten variants for each content format and settled on 55% diagram, 25% editorial composition and 20% dimensionality. A subsequent pass replaced 20 covers to broaden documentation, database, network, runtime and branching subjects while retaining title-based assignments. The original artwork refinement record does not state its delivery date.

The approved balanced samples remain inputs to active generation records. Portable original source filenames and full prompts are retained for reproducibility. Superseded UI boards and preview screenshots are not production artwork.

## Branding and Linux visual validation — 2026-09-13

Upstream and the Simple Flow symbol superseded Relay explorations. The approved raster reference informed directly rebuilt SVG geometry; it is not a runtime logo image. The login tagline is “Share what you learn.”

A later visual failure reproduced a macOS/Linux rendering difference: the mobile home page was 1581px tall in the macOS baseline and 1605px in the pinned Linux browser. All 72 baselines were regenerated and reviewed in the Linux image; a subsequent comparison with updates disabled passed. This is dated validation evidence, not a standing guarantee. Committed baselines must be generated and checked in the pinned CI environment.
