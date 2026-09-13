# Developer technical editorial artwork

Upstream uses **40 covers: ten each for videos, articles, courses, and paths**. The collection follows a technical publication and architecture diagram style: **55% diagram, 25% editorial composition, 20% dimensionality**. Lighter slate backgrounds, silver construction lines, layered graphite surfaces, softly lit edges, and restrained format accents keep diagrams readable.

Every format uses the same drafting brief: slate `#1c2935`, a faint square grid, fine silver strokes, quiet secondary lines, subtle illumination at focal points, and minimal visual noise. Views are orthographic or restrained isometric. Courses use shallow software service modules and schemas; articles use flatter code and documentation surfaces. Videos depict runtime behavior and paths use Git progression. Physical hardware, machinery, and generic engineering subjects are excluded. Vary the main silhouette, arrangement, and direction within each format while keeping this shared visual language.

| Format | Metaphor | Visual language |
| --- | --- | --- |
| Video | See it run. | Coral execution traces, debugging, packets, request/response flows |
| Article | Understand the idea. | Amber annotations, code reviews, documentation layers, references |
| Course | Build the system. | Blue service modules, software stacks, schemas, dependencies |
| Path | Follow the progression. | Violet branches, milestones, routes, state transitions |

## Format recognition and subject variety

The refinement replaces 20 covers and retains the other 20 byte-for-byte. Each format has a dominant structure: articles explain through documentation and annotations; videos depict execution over time; courses assemble connected systems; paths follow milestones, branches and states. Color reinforces these structures rather than supplying the only distinction.

| Format | Refined variants | Subjects |
| --- | --- | --- |
| Article | 1, 2, 4, 5, 6, 8 | API reference, schema explanation, protocol documentation, query plan, test specification, runbook |
| Course | 1, 3, 5, 6, 7, 8 | Event-driven system, databases, component assembly, identity architecture, storage, distributed network |
| Video | 2, 4, 5, 8 | Packet transit, streaming buffer, test execution, rendering frames |
| Path | 2, 5, 7, 9 | Learning milestones, debugging states, prerequisite graph, merge tree |

Keep code-panel-led compositions to at most three per format. Use short labels, meaningful annotations and sparse supporting code only. Avoid framing every element in a floating panel. Documentation pages remain appropriate for articles. Keep important subjects within the central 65% of image height and 85% of width. Review silhouettes without badges and in grayscale as well as at card size and banner crops.

## Review the full collection

Each sheet shows variants 0–9 in reading order. All variants, including the four signature illustrations, use the approved balanced editorial treatment.

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

All 80 responsive assets are saved in `frontend/react/public/artwork/`: `{type}-{0..9}.webp` at 1280×720 and `{type}-{0..9}-card.webp` at 640×360. Each full image stays below 200 KB and each card below 60 KB. Image URLs include `?v=refined-1` to refresh cached old artwork. Lazy loading, responsive sources, reserved dimensions, and local failure recovery are preserved. The four `-technical` signature assets remain available as aliases of variant 0 and use the same updated artwork.

## Generation

Generated with the built-in image generation tool. The 20 refinements use the approved samples as style references, with two corrective edits for course banner framing; earlier retained outputs also include targeted corrective edits. [Final prompts and source records](generation-record.json) identify all forty selected outputs. Source records store portable PNG filenames only, without machine-specific paths. Re-export with `python docs/artwork/export_technical.py --source-dir <generated-images-directory>` (requires Pillow and the original generated PNG files). The source directory is supplied at runtime and is never written to the records. Export only resizes and encodes the generated artwork and assembles review sheets. No generation occurs at runtime.

The illustration files are bundled locally; no database or content changes are required.

## Verification

The 20 replacements were reviewed at 320×180, without badges, in grayscale, and in wide banner crops. All 40 covers were reviewed together for consistent style and format identity. Fingerprint checks confirm the other 20 covers and signature aliases remain byte-for-byte unchanged. The 80 responsive files total 1,834,188 bytes and pass dimension and byte-budget checks. Source records use portable filenames; a project-file audit found no machine-specific paths.

Frontend type checks, lint, 39 unit tests and the production build pass. All 66 mocked browser scenarios pass, with refreshed screenshots at 390, 768 and 1440 pixels; no application database was involved.
