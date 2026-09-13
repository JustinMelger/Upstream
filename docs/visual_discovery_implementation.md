> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# Visual discovery implementation

Upstream now uses the approved visual-library direction: horizontal navigation, recognizable resource artwork, personal learning collections, and a friendly sharing editor. The reference mockups remain in [the design directory](mockups/discovery-direction/README.md); illustrative data was not imported into the application.

The follow-up [supporting pages implementation](supporting_pages_implementation.md) extends this direction to details, paths, Activity, Profile, and Admin, including Activity excerpts and focused account dialogs. Its validation record supersedes the original release counts below.

The later [artwork expansion](artwork/README.md) supplies forty covers (ten per type); the original twelve-cover milestone below is historical.

## Delivered behavior

- A 64px top header replaces the sidebar. Navigation and advanced filters use accessible drawers below 900px. Content has a 1440px outer cap and responsive four/three/two/one-column discovery grids.
- Forty bundled artwork variants (ten per type), each in 640px and 1280px WebP, are selected deterministically from type and normalized title. The pre-expansion catalog retains its covers through a compatibility map; see the [artwork library](artwork/README.md). All full-size files are below 200KB, card variants below 60KB. Decorative artwork has CSS fallbacks, dimensions reserved before loading, and lazy loading away from the first hero. Titles remain HTML, and contributors use initials.
- Explore promotes one item from the current first page into a compact spotlight. It prefers the first recommendation note, falls back to the first item, and removes that item from the grid. Existing counts/pagination cover both presentations. Search, filters, other sorts, and later pages suppress the spotlight.
- My learning retains deterministic next-course selection, opens usable course URLs directly, and provides a details link. Contextual status actions and an accessible status menu retain the previous server state on failure. Selected-path progress remains course-only and independent of manual path status. One additional bounded read supplies the default collection's selected-path preview.
- Details group artwork, title, summary, ratings, resource access, and progress controls before long content. Recommendation attribution, reviews, deep links, ownership checks, and destructive-action confirmation remain.
- Share/edit provides a four-type chooser, live desktop publication preview, mobile preview disclosure, optional descriptions, recommendation notes, path ordering, and existing validation. Draft restore/discard and type changes update the preview. Saved copy appears only after successful browser-storage persistence. Credentials and server-side drafts are not introduced.
- Activity, Profile, Login, and Admin use the same navigation and visual vocabulary while preserving their capabilities.

## Data and compatibility

Migration `20260909_0019` adds nullable `articles.description` and a 2,000-character database constraint. New/edit API contracts accept optional plain text, trim whitespace, preserve omitted values, and clear explicit null/blank values. Summaries propagate through catalog/search, personal collections, details, and embedded path items. Existing video descriptions are reused without new limits.

`LearningSummary.next_course` now includes optional URL, provider, duration, and current-user status from bounded SQL queries; the selection and tie-breakers remain unchanged. OpenAPI and TypeScript contracts are regenerated. Shared catalog responses still contain no personal path progress.

No image uploads, external preview fetching, cover-selection storage, runtime image generation, autoplay, Teams, universal completion, or new analytics were added.

## Verification

Verification passes: 168 isolated PostgreSQL backend tests, 26 frontend unit tests, 18 browser scenarios, and 27 visual comparisons against reviewed baselines. Frontend unit coverage includes deterministic artwork assignment and budgets, image failure recovery, one-link cards, unpublished previews, and single-page pagination. Browser coverage includes the retained workflows plus spotlight uniqueness, filter/page history, bounded reads, and live preview/draft/article-summary persistence. Visual snapshots cover nine screen/state variants at 390px, 768px, and 1440px.

Backend lint, formatting, typing, import contracts, generated OpenAPI contract checks, frontend lint, TypeScript checks, and production builds also pass.

Fresh-database migration and populated legacy migration pass. The populated check compares original IDs, authors, reviews, selections, tracking, path order, and retained team records. Existing article summaries remain null until supplied.

## Local release and rollback

The local preview is http://localhost:18080 using the existing disposable demo database. It must be rebuilt when frontend source changes; restarting an old Nginx image alone cannot update assets. The regular Docker deployment remains `docker compose up --build -d`, including the additive migration service.

Previous local images were preserved as `learning-react-ui:before-discovery` and `learning-react-api:before-discovery`. Roll back images without dropping the new nullable column, so new descriptions survive. Production deployment is separate and has not been performed.
