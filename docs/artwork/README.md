# Developer technical editorial artwork

Learning Hub uses **40 covers: ten each for videos, articles, courses, and paths**. Every previous cover has been replaced with the approved dark technical editorial style: fine drafting grids, silver construction lines, translucent smoked glass, and restrained format accents.

| Format | Metaphor | Visual language |
| --- | --- | --- |
| Video | See it run. | Coral waveforms, execution traces, packets, request/response flows |
| Article | Understand the idea. | Amber annotations, code reviews, documentation layers, references |
| Course | Build the system. | Blue service modules, software stacks, schemas, dependencies |
| Path | Follow the progression. | Violet branches, milestones, routes, state transitions |

## Review the full collection

Each sheet shows variants 0–9 in reading order. Variant 0 retains the approved signature illustration for that format.

### Videos

![Ten technical video covers](video-collection.webp)

### Articles

![Ten technical article covers](article-collection.webp)

### Courses

![Ten technical course covers](course-collection.webp)

### Paths

![Ten technical path covers](path-collection.webp)

## Assignment and delivery

`ResourceArtwork` selects a stable variant from the content type and normalized title. The existing title fingerprint compatibility map preserves established variant assignments. The same resource receives the same cover across cards, spotlights, previews, and detail pages. Titles and metadata remain accessible HTML; artwork is decorative and does not claim to depict a resource's exact contents.

All 80 responsive assets are saved in `frontend/react/public/artwork/`: `{type}-{0..9}.webp` at 1280×720 and `{type}-{0..9}-card.webp` at 640×360. Each full image stays below 200 KB and each card below 60 KB. Image URLs include `?v=technical-2` to refresh cached old artwork. Lazy loading, responsive sources, reserved dimensions, and local failure recovery are preserved. The four earlier `-technical` signature assets remain available as aliases of variant 0.

## Generation

Generated with the built-in image generation tool, one call per illustration. [Final prompts and source records](generation-record.json) identify all forty selected outputs. Source records store portable PNG filenames only, without machine-specific paths. Re-export with `python docs/artwork/export_technical.py --source-dir <generated-images-directory>` (requires Pillow and the original generated PNG files). The source directory is supplied at runtime and is never written to the records. Export only resizes and encodes the generated artwork and assembles review sheets. No generation occurs at runtime.

The illustration files are bundled locally; no database or content changes are required.

## Verification

All forty covers were reviewed at card size. The 80 active responsive files total 2,341,442 bytes. Frontend type checks, lint, 39 unit tests, and the production build pass. All 66 mocked browser scenarios pass at 390, 768, and 1440 pixels, with refreshed visual baselines. API data is mocked during these checks; no application database is modified.
