# V1 artwork library

Learning Hub bundles **40 covers: ten each for courses, articles, videos, and paths**. Variants 0–2 are the original assets; variants 3–9 add 28 generated compositions. All resource titles, descriptions, and author information remain HTML. Artwork is decorative and does not represent a resource's actual content or provider branding.

## Collections

### Courses — blue architecture and spaces for learning

![Ten course covers](course-collection.webp)

The new set adds an observatory, curved museum interior, glass bridge, engineering workshop, arched courtyard, lakeside pavilion, and geometric atrium.

### Articles — amber editorial scenes

![Ten article covers](article-collection.webp)

The new set adds an open notebook, sculptural book, reading nook, paper spiral, hourglass still life, paper arches, and an unfurling scroll.

### Videos — coral studio and light compositions

![Ten video covers](video-collection.webp)

The new set adds a glass ribbon, suspended discs, ribbon wave, sphere and prism, acoustic wall, illuminated torus, and interlocking ceramic loops.

### Paths — lavender journeys

![Ten path covers](path-collection.webp)

The new set adds a lake crossing, garden stairway, forest boardwalk, canyon bridge, coastal trail, mountain pass, and garden labyrinth.

## Assignment and delivery

New titles use the existing type-and-normalized-title hash across ten variants. The pre-expansion local catalog's 12 title fingerprints retain their original assignments through `artwork-legacy.json`; it contains only fingerprints and variant indices. Keep this compatibility map and the original assets when changing the library. Title changes may select another artwork, as before. New installations use the same deterministic rules, with no browser storage, per-item requests, image picker, or database columns.

Assets live in `frontend/react/public/artwork/` as 1280×720 full-size and 640×360 card WebP files. All 80 files together occupy 6,857,672 bytes. The largest full-size file is 199,532 bytes; the largest card is 59,136 bytes, within the existing 200KB/60KB budgets. Existing responsive sources, lazy loading, reserved aspect ratios, and CSS failure fallback remain in place.

The collection sheets above are review artifacts and are not loaded by the application. [Generation record](generation-record.json) identifies the source outputs and creative briefs for the additional artwork. The stray upper-left mark in article-7 was removed before export. Generation occurs only during development, never at runtime.

## Verification and local release

Review covers all forty assets at card size plus populated desktop/mobile screens. Unit coverage checks that all ten variants per type resolve to existing files within byte budgets, that normalized titles are consistent, that an established resource keeps its cover, and that failed artwork recovers through the local fallback. Verification passes: 39 frontend unit tests, 33 browser scenarios, and 66 reviewed visual comparisons at 390px, 768px, and 1440px. Frontend lint, formatting, typing, and production build checks also pass. Browser and visual regression coverage retain the existing product flows.

The frontend image is rebuilt and the preview refreshed at http://localhost:18080. Existing content and tracking data are unchanged. The previous UI image is retained as `learning-react-ui:before-artwork-expansion`; the backend is unchanged. Custom image uploads remain outside v1, pending user feedback.
