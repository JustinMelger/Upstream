# Discovery direction mockups

Concept mockups generated with the built-in image generation tool. These are visual proposals, not implemented interfaces. Artwork, identities, ratings and content are illustrative.

- [Explore](explore.png)
- [My learning](my-learning.png)
- [Share](share.png)

Follow-up [supporting-page mockups](../supporting-pages/README.md) cover resource details, paths, Activity, Profile, and Admin with paired desktop/mobile layouts.

Implementation considerations: keep search results compact (omit the feature banner while filtering); use real available resource imagery and designed text-based fallbacks; retain accurate course-only path progress (the generated illustration incorrectly draws five segments for four courses); compute character counters from actual input; keep hero images compact on mobile; do not add automatic artwork generation, featured-content administration, or avatar upload implicitly. Prefer consistent artwork for the same resource. The Share image's photographic fallback is exploratory; a reusable typographic fallback must also be designed. Top navigation replaces the sidebar as a proposed design change.

## Reconstructed design briefs

The original mockup prompt save failed. These briefs reconstruct the approved intent; they are not represented as exact original prompts. The mockup PNGs above are unchanged.

### Explore

High-fidelity dark Learning Hub catalog, original branding, compact top navigation, pale-blue primary actions, warm content accents. A compact recently shared resource spotlight above a searchable filterable grid, artwork-led resources, accurate ratings and human recommendation excerpts. Prime Video-inspired visual discovery with IMDb clarity and Goodreads personal connection.

### My learning

Use the same navigation, typography, palette, and artwork style. Show one visual Continue learning panel, course status collections with contextual actions, and an independent selected-path course-progress preview. No playback timeline, streaks, or individual-course percentage.

### Share

Use the same design system. Pair a friendly form with a publication preview. Lead with resource essentials, learning value, and a personal recommendation, with optional metadata secondary. Reflect session draft recovery and use no fictional rating on unpublished content.

## Implemented cover library

The twelve standalone covers were generated with the built-in image generation tool. Exact cover prompts and source-image provenance are saved in the twelve adjacent `course-*.txt`, `article-*.txt`, `video-*.txt`, and `path-*.txt` files. Optimized assets are bundled in `frontend/react/public/artwork/` with full-size and card-size WebP variants. They contain no resource titles; the frontend renders titles and metadata in HTML. No image-generation service runs inside the application.

Cover provenance uses generation-session and source-image identifiers, not local filesystem paths. These identifiers record the original generation output; the portable, optimized assets live in `frontend/react/public/artwork/`.
