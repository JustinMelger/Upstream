> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# Frontend UX refinement

This records the preceding refinement release. The [visual discovery release](visual_discovery_implementation.md) supersedes its sidebar, layout, and card presentation.

This release builds on the React redesign and centers the workspace on resuming learning, choosing a useful next step, and understanding personal progress. It retains the existing content, accounts, permissions, URLs, and tracking model.

## Delivered experience

- Semantic blue/slate tokens with warm article, video, and path accents; readable secondary text, explicit control borders, 36px/28px page titles, a 64px header, and 44px primary interaction targets.
- Compact next-step guidance in My learning, counted status links, inline course/path status controls, local mutation errors, and personal course-only path totals. Contributions remain secondary.
- Debounced URL search, searchable provider/category options, removable filter chips, and a mobile filter drawer with staged Apply/Cancel. Catalog links retain their return context. Tablet content stacks where the persistent sidebar leaves insufficient reading width.
- Detail actions precede long content on smaller layouts. Author-attributed notes remain prominent; existing reviews appear before the form, with an action that focuses the review input.
- For you, Shared activity, and My stats replace nested Activity controls. Feeds contain no private progress; review events open review deep links. Personal counts appear in My stats and link to learning collections.
- Sharing/editing groups essentials, optional metadata, recommendation notes, and path sequencing. Validation focuses the first invalid field; note counters and keyboard-reordering announcements provide immediate feedback.

## Draft lifecycle

Versioned sessionStorage keys include the authenticated username, content type, and new/edit ID. Snapshots contain only named content fields and ordered path references. They debounce by 500ms and flush on navigation/pagehide; the last keystroke is retained even when React removes the form.

Reopening offers Restore draft or Discard draft. Published content is never silently replaced by a saved edit. Successful publication or discard removes the draft; explicit logout/account changes also clear pending saves so cleanup cannot resurrect them. Expiration preserves the draft for the same account after sign-in. Drafts are local to the browser session and do not synchronize between devices.

Storage failures leave forms usable with an explanatory notice. Credentials are never stored. Server-side validation remains authoritative, including when restored path references have been deleted; the user can remove those references and retry without losing the form.

## API changes

- Authenticated `GET /catalog/facets` returns the existing paginated envelope with string options. `field` is provider/category; `option_q` searches options. Catalog filters apply except the facet's own selected value. Default page size is 24, maximum 100.
- `GET /learning/items` uses a personal LearningItem contract with nullable `course_progress: {completed,total}`. Selected paths get scoped totals through one extra SQL query for the bounded page. Shared catalog responses do not contain this field.
- OpenAPI and TypeScript contracts are regenerated. No database migration, bookmark feature, article/video completion, or historical analytics is introduced.

## Verification and release

Validation uses isolated PostgreSQL databases and the pinned Linux Playwright environment. Coverage includes facet filtering/authentication/pagination, path-progress privacy, draft debounce/navigation/identity/logout/storage failures, expired-session recovery, stale references, inline status recovery, mobile filters, catalog return state, validation focus, review focus, and 390×844 next-action/list visibility.

Implementation verification: 166 backend tests, 21 frontend unit tests, 16 browser scenarios, and 21 visual comparisons passed. Python lint, formatting, typing, import contracts, OpenAPI consistency, frontend lint/formatting, and production builds passed. Visual baselines were reviewed at all three widths, including the tablet layout with its persistent sidebar.

The release retains the existing Docker deployment and rollback workflow. The local preview uses the disposable demo database; production deployment remains separate. Updated visual baselines cover populated, empty, loading, and error states at 390px, 768px, and 1440px. CI compares them without auto-accepting changes.

## V1 sharing follow-up

New resource sharing now includes optional [Fetch details](metadata_autofill_implementation.md), preserving user input, session drafts, and publication review. Paths and editing remain manual.
