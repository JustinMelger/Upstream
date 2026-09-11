> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# Supporting pages implementation

The approved [supporting-page mockups](mockups/supporting-pages/README.md) now guide resource details, mixed learning paths, Activity, Profile, and user administration. The existing Explore design, global navigation, artwork assignment, and product permissions are retained.

## Delivered behavior

- Resource introductions place copy/actions beside artwork on desktop and use a 72px thumbnail below 900px. Mobile actions precede extended metadata. Course/article/video links read Open course, Read article, and Watch video; only courses expose tracking. A short description appears once; descriptions longer than 240 characters have a bounded introduction and complete text below. Recommendations are attributed and prominent. Reviews retain forms, owner/admin removal, dates, focus actions, and deep links. Failed review reads do not masquerade as zero reviews.
- Paths show ordered mixed resources with deterministic thumbnails and visible course-status labels at every width. Personal completion is a continuous course-only progress bar; manual path status remains independent. Empty and zero-course paths remain usable. Existing embedded resources and one personal progress read supply the page without per-item HTTP calls.
- Activity uses 144×81px desktop and 72×72px mobile thumbnails, explicit contributors/types/timestamps/ratings, and attributed text excerpts. For you remains the default; Shared activity and My stats preserve existing URL behavior and privacy. Stats remain current personal totals.
- Profile presents private account identity, linked personal totals, and three latest contribution cards using the existing bounded collection endpoint. Identity, totals, and contribution recovery are independent. No public profile or new social data is introduced.
- Admin has alphabetical account rows, case-insensitive username search stored in the URL, responsive account cards, and Radix Manage menus. Create/reset dialogs preserve inputs after recoverable errors. Disable/enable and deletion retain existing server policies. Self-disable/delete remain unavailable; dialog closure restores focus, and deleting an account returns focus to account search.

## API and data

`ActivityEvent` adds nullable `excerpt` (maximum 280 characters) and `excerpt_kind` (`recommendation`, `description`, or `review`). Share projections prefer nonblank recommendation notes, then descriptions; review projections use review text. SQL trims blank fields, and the service bounds outgoing text with an ellipsis included in the limit. Empty text has no kind. These are current-record projections, not immutable history. Existing merged ordering, pagination, authorization, and bounded query count are preserved.

OpenAPI and TypeScript contracts are regenerated. There are no new endpoints, database migrations, media assets, or mutation contracts in this release.

## Validation

- Backend: 172 tests pass, including all four content types' share/review excerpts, precedence, truncation, current-record updates, personal filtering, and pagination. Existing bounded-query tests remain passing.
- Frontend: 26 unit tests and 24 browser scenarios pass. New browser coverage exercises mobile actions, long descriptions, failed artwork, unavailable ratings, failed tracking recovery, path privacy/request boundaries, Profile partial failures, Admin restrictions, dialog input preservation, and focus restoration.
- Visual review covers 51 baselines: 17 screen/state variants at 390px, 768px, and 1440px, including all resource types, paths, Activity views, Profile, Admin and its creation dialog, plus existing Explore/My learning/Share and recovery-state coverage. All 51 final comparisons pass against the reviewed baselines.
- Backend lint/format/type checks and both import-boundary contracts pass. Frontend lint/format checks, generated-contract verification, and production image builds pass.

## Differences from the illustrations

Actual permissions and content replace illustrative values. Existing explicit Add to My learning / Remove from My learning labels are retained for path selection. Review forms remain present below reviews; authorized review removal and content edit/delete actions remain available. Admin forms open in focused dialogs instead of occupying permanent page space. Course-status text remains visible on mobile. Activity thumbnails are intentionally smaller than the initial board.

## Local release and rollback

The frontend and backend images are rebuilt through the existing Docker workflow. The local preview remains http://localhost:18080 and uses its existing disposable demo database without reseeding. Previous images are retained as `learning-react-ui:before-supporting-pages` and `learning-react-api:before-supporting-pages`. Rollback replaces images only; no schema rollback is needed. Production deployment is not performed.

## Course journey follow-up

Course details and My learning now use the explicit Add / Start / Continue / Complete flow documented in [Course journey implementation](course_journey_implementation.md), including persistent completion feedback and Undo. This follow-up supersedes the earlier course action labels while retaining the supporting-page layout.
