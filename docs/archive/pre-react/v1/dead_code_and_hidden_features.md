# Dead Code And Hidden Features

This document separates:

- code that is clearly stale or non-canonical
- implemented features that are real but weakly surfaced
- v1 features that should now be removed or hidden based on release scope decisions

## 1. Stale Or Non-Canonical Code

### Old `/teams` page route

Current state:

- the obsolete page-level route implementation in `pages/activity/page.py` has been removed
- the shared `pages/activity` helper modules remain because the canonical Teams page still uses them

Interpretation:

- the duplicate `/teams` route is no longer part of the shipped app
- the remaining `activity` package is shared UI/domain support code, not a second page surface

## 2. Hidden But Real Features

### Recommendations

Current state:

- recommendation UI has been removed from the released frontend
- recommendation backend APIs have been removed from the live app surface
- dormant recommendation table/models still exist in the persistence layer

Interpretation:

- recommendations are not part of the shipped v1 product
- remaining recommendation persistence artifacts are cleanup debt, not release scope

V1 decision:

- recommendations are out of v1
- ratings/reviews remain the social signal kept for release

Action:

- keep recommendation behavior out of the release narrative
- leave table/model cleanup as a post-v1 persistence decision

### AI Curator

Current state:

- real backend route exists
- UI route exists behind a feature flag
- behavior is draft-only and deterministic

Interpretation:

- this is an experimental feature, not dead code
- it should not be presented as a stable product feature in v1

Action:

- keep feature-flagged or disable in release
- do not include it in the core v1 product narrative

## 3. Keep Internally But Do Not Market As Core Product

- URL metadata/autofill support in share flows
- notification/activity composition infrastructure
- frontend helper packages that support Explore/Teams/Home but are not top-level routes

These are implementation-level capabilities, not the main product story.

## 4. Recommendation Cleanup Map

If the v1 decision is “reviews yes, recommendations no”, the affected areas are:

### Backend

- recommendation endpoints, services, repositories, and derived activity behavior have been removed from the live app surface
- recommendation table/model cleanup is still a separate persistence follow-up if desired

### Frontend

- recommendation card/menu actions have been removed
- recommendation summaries and “recommended for you” copy have been removed

### Docs

- roadmap references to recommendations as a core capability
- architecture docs that describe recommendations as part of the current product contract
- v1 docs and release notes

## 5. Suggested Execution Order

1. Remove recommendation language from v1 docs.
2. Remove recommendation UI and backend APIs from the released surface.
3. Clean up stale route/page code.
4. Decide whether dormant recommendation persistence artifacts should be deleted after release.

## 6. Removal Rule

For v1 cleanup:

- remove stale route implementations that are not canonical
- hide or disable implemented-but-cut features from the user-facing app
- only delete deeper backend/data code when the removal is intentional and fully mapped
