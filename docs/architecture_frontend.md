# React frontend architecture

The Upstream frontend is a Vite-built React application in `frontend/react`.

## Boundaries

- `src/app`: application providers, route tree, authentication boundary, responsive shell.
- `src/components`: reusable visual and interaction primitives.
- `src/features`: separate My learning (`learning.tsx`), Activity (`activity.tsx`), and Profile (`profile.tsx`) pages alongside Explore, authentication, details, sharing, and administration. Routes import these pages directly.
- `src/features/sharing/ItemPicker.tsx`: the path editor’s catalog picker and selected-item prop type. Publication, form values, drafts, and metadata suggestions stay in the Share page.
- `src/features/details/Reviews.tsx`: review display, form, mutations, and deep-link focus behavior. The detail page still owns fetching the resource and review list.
- `src/lib/api`: fetch/error/CSRF boundary, generated OpenAPI contracts, ID and URL helpers.
- `src/styles`: shared tokens and baseline; CSS Modules own component/page styling.

TanStack Query owns server state and invalidation. Filters and pagination use URL parameters. Forms keep input locally and recover share/edit drafts from versioned sessionStorage scoped to account, content type, and new/edit identity. Draft writes debounce by 500ms and flush on navigation/pagehide. Explicit logout/account changes clear drafts; expiry preserves them for the same account. Credentials never enter storage. Route changes preserve deep-link contracts. The backend remains authoritative for authorization and content validation.

## Stylesheet ownership

Shared UI primitives own `src/components/ui.module.css`, including headings, loading/empty states, pagination, statistics, and dialog controls. Other consumers import these shared styles directly; shared components do not depend on feature styles.

My learning, Activity, and Profile own their exclusive styles in neighboring CSS Modules. `pages.module.css` retains shared layouts and styles for the remaining features; `supporting.module.css` retains common detail/review sections and administration styles. My learning composes shared tabs, active-state, and action classes to preserve both base styling and page-specific descendant rules. Keep media-query order and specificity intact when extracting further rules.

The collection card stays local to My learning. Query keys, invalidation and URL state remain with their original page/component owners. No shared query abstraction or feature barrel is introduced.

## Sessions

Nginx serves React and proxies `/api` to FastAPI. Credentials live in HttpOnly cookies. The session endpoint supplies user metadata and a session-bound CSRF token. Mutations send that token and the browser's Origin. A 401 clears cached personal data and returns the user to login with a validated internal return URL.

## Product pages

My learning (`/home`) is action-focused. Explore is the shared catalog. Activity has For you, Shared activity, and My stats views; personal totals appear only in My stats. Profile contains account information; Admin manages users. Sharing and details reuse subtype-aware forms and controls. Only courses support tracking. Mixed-path progress explicitly counts courses and does not set manual path status automatically.

No shared feed exposes users' private progress. Compatibility redirects are documented in [operations](operations.md#routes).

## Verification

TypeScript compilation, ESLint, Vitest interaction tests, generated contract drift checks, and Playwright workflows run in CI. Browser data is seeded into a disposable PostgreSQL database. Test desktop, tablet, and mobile sizes plus keyboard focus and retained form input. Deployment has a separate API image and static Nginx UI image.

## Navigation and interaction

Semantic tokens own the blue/slate palette, warm subtype accents, control boundaries, and text colors. The shell uses a 64px horizontal navigation header and a 1440px outer content cap. Navigation moves into a drawer below 900px. Main page titles are 40px desktop / 28px mobile. Interactive controls and primary content links have 44px targets.

My learning exposes course status inline, with independent path status and course totals supplied by the personal read model. Counts link to filtered collections. Failed mutations retain the server's previous status and show a row-local error.

Explore keeps filters in URLs. Text search replaces history after 300ms; explicit filter/page changes push history. Provider/category choices come from a bounded facet endpoint. Below 900px the filter drawer stages provider/category/sort changes until Apply. Cancel leaves the URL untouched. Content links carry catalog return context in router state; existing review deep links remain valid.

Draft restoration always asks before replacing the form. Form snapshots include named content fields and ordered path references, excluding credentials and unrelated picker searches. Storage failure leaves editing available with an explanatory notice. Server validation remains authoritative for stale references.

See [operations](operations.md#visual-regression-checks) for the pinned browser workflow.

## Artwork and resource presentation

Resource artwork comes from forty bundled local covers (ten per resource type) with 640px and 1280px WebP variants. Type and normalized title determine the variant consistently across Explore, details, My learning, and live Share previews. CSS fallbacks handle failed images. Explicit Fetch details is available on new course, article, and video forms; image uploads remain outside v1.

Explore promotes one resource from its existing first catalog page into a compact spotlight; it does not repeat that item in the grid or change pagination totals. Search, filters, non-default sorting, and later pages hide the spotlight. My learning opens the deterministic next course URL directly when valid and exposes contextual progress actions. A single bounded selected-path preview is optional beneath the default course collection.

Article summaries use an optional description field. Share/edit previews derive from current form values and update after draft restoration/discard; only a successful sessionStorage write displays the saved message. See [artwork guidance](artwork/README.md) for exports and assignment rules.
