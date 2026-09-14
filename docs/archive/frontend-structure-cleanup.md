# Frontend structure cleanup — 2026-09-14

This records the focused pre-pilot cleanup. Use the [current frontend architecture](../architecture_frontend.md) for ownership guidance and [operations](../operations.md) for check commands.

## Delivered boundaries

- Replaced the combined workspace module with dedicated My learning, Activity, and Profile pages. Routing imports each page directly, including Explore. The collection card remains local to My learning.
- Extracted the sharing-owned path item picker and detail-owned reviews component. Form publication, metadata suggestions, draft recovery, and parent queries retain their existing owners.
- Moved shared primitive styles into a component-owned CSS Module. Shared UI no longer imports feature styles. My learning, Activity, and Profile now own their exclusive styles; genuinely shared layout and remaining feature styles stay in the existing modules.
- Preserved responsive rule order and specificity. My learning composes the shared actions, tabs, and active-state classes. Facet pagination styling uses its existing accessible navigation label across the component boundary.
- Removed unused imports, the Explore forwarding export, the collection card's unused public export, and two ineffective local selectors for globally applied `eyebrow`/`button` classes. Existing shared components and API types were retained.

The shared page stylesheet decreased from 1,516 to 1,176 lines; supporting styles decreased from 517 to 333. This is a partial ownership cleanup, not a full stylesheet or form redesign.

## Verification

- Formatting, ESLint, TypeScript, and production build passed.
- All 39 frontend unit tests passed.
- All 33 browser workflows passed across the final full run (32) and focused admin rerun (1) against the disposable browser database, covering learning status and completion, Activity, Profile, reviews, sharing, path ordering, administration, and draft recovery.
- All 72 pinned visual comparisons passed at 390px, 768px, and 1440px without baseline updates.
- OpenAPI export check passed; regenerated TypeScript output was byte-identical. API contracts and lockfiles are unchanged.
- A TypeScript syntax-tree comparison confirmed that all six moved function bodies are identical apart from stylesheet bindings.

The first browser run overlapped with a formatting pass and was disrupted by development hot reload; it was discarded and rerun against stable final source. That interrupted run left its `browser_member` account behind; the subsequent admin scenario encountered duplicate protection. Only that account, identified by its exact creation timestamp, was removed before rerunning the admin scenario. CSS composition causes Vite's PostCSS pipeline to emit a missing-`from` warning; compilation, responsive rendering, and visual checks pass. No dependency or toolchain change was included to address that warning.

## Preserved scope and follow-up

Appearance, card sizing, branding, artwork, routes, requests, query keys, invalidation, permissions, and storage keys remain unchanged. No backend changes, migrations, production deployment, or local preview refresh were included. The pre-existing untracked mockup directory was left untouched and excluded from the commits.

Defer further splitting of the large Share form, the remaining page/detail/admin styles, query abstractions, and collection/card UX changes until separate work informed by pilot feedback.
