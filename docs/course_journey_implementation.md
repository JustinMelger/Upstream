> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# Course journey implementation

The course journey now reads **Find or share → Add to My learning → Start → Continue → Complete**, preserving the approved discovery design and personal tracking privacy.

## Delivered behavior

- Untracked course details offer Open course and Add to My learning separately. Adding saves Interested and links to that collection. Sharing does not create tracking: successful publication opens details with an explicit invitation to add the course; edits confirm Changes saved.
- Interested courses use Start learning, saving In progress before opening the external resource. In-progress courses use Continue learning; completed courses use Open course without resetting completion. The existing deterministic next-course selection also supports starting an untracked path suggestion without changing path selection or manual status.
- Starting reserves a new tab during the click and removes its opener. A failed save closes that tab and preserves the previous status. Blocked or unavailable tabs leave a usable Open course link after saving. Invalid or absent URLs use View details, with status changes available independently.
- In-progress courses expose Mark completed alongside their status menu. All transitions and removal remain available. Contributions do not infer a personal status from a response that does not contain one.
- Completion preserves the current URL and shows Course completed. Nice work! with Undo, View completed, and Review course. Undo restores the immediately preceding status and supports retry after failure. The notice remains after a card leaves the current collection; keyboard focus moves there when the affected card disappears.
- Interested, In progress, and Completed have contextual empty states. The finished-in-progress message follows a successful completion in this session, not an inference from historical data after reload.

## State and interfaces

`course-journey.tsx` supplies shared actions for details, collection cards, and the next-course panel, plus an authenticated shell feedback region outside cards. Notices and Undo are held only in memory and survive internal navigation until dismissal, a successful replacement action, logout/account change, or reload. Duplicate mutations are blocked per course; errors stay local to the initiating controls. Course behavior remains separate from path-status mutations.

Existing tracking mutations and bounded personal reads are reused. Successful changes refresh tracking, collections, summary totals, and course-only path progress. There are no backend schema changes, migrations, new endpoints, per-card reads, or API contract changes.

## Verification

Coverage includes explicit adding, publication independent of tracking failure, synchronous tab reservation, failed-save tab closure, blocked popup recovery, invalid URLs, reopening completed courses without mutation, completion without navigation, recoverable Undo, path suggestions, focus recovery, and notice lifetime.

- 172 backend tests and 32 frontend unit tests pass.
- 30 browser scenarios cover the journey and retained sharing, drafts, permissions, navigation, and supporting-page flows.
- 60 visual comparisons cover 20 screen/state variants at 390px, 768px, and 1440px. Added states show adding, completion, and popup recovery; existing discovery, details, Share, Activity, Profile, and Admin coverage is retained.
- Frontend lint, formatting, TypeScript/production build, backend Ruff/mypy, import boundaries, and unchanged OpenAPI verification pass.

The reviewed notice wraps on mobile and preserves the established palette and restrained feedback treatment. No confetti, automatic review navigation, new progress model, or historical analytics are introduced.

## Local preview and rollback

The local preview at http://localhost:18080 uses the rebuilt frontend image and the existing backend and database. Data is preserved without reseeding. Previous images are retained as `learning-react-ui:before-course-journey` and `learning-react-api:before-course-journey`; rollback changes images only. No production deployment is performed.
