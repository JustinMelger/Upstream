# Dead Code And Hidden Features

This document separates:

- code that is clearly stale or non-canonical
- implemented features that are real but weakly surfaced
- v1 features that should now be removed or hidden based on release scope decisions

## 1. Stale Or Non-Canonical Code

### Old `/teams` page route

Current state:

- [frontend/ui/nicegui/pages/activity/page.py](/Users/justinmelger/Desktop/github/learning-platform/frontend/ui/nicegui/pages/activity/page.py:27) still defines a full `/teams` page.
- [frontend/ui/nicegui/pages/teams/page.py](/Users/justinmelger/Desktop/github/learning-platform/frontend/ui/nicegui/pages/teams/page.py:21) also defines `/teams`.
- [frontend/ui/nicegui/main.py](/Users/justinmelger/Desktop/github/learning-platform/frontend/ui/nicegui/main.py:37) registers the `teams` page, not the `activity` page.

Interpretation:

- the old page-level route in `pages/activity/page.py` is stale
- the entire `activity` package is not dead, because some helpers are still reused by the canonical Teams implementation

Action:

- remove or archive the old `activity/page.py` route implementation
- keep reused helper/view-model modules only if the canonical Teams page still depends on them

## 2. Hidden But Real Features

### Recommendations

Current state:

- backend recommendation APIs exist for courses and paths
- recommendation summary data feeds list/detail/home surfaces
- UI actions exist, but mostly as secondary menu/dialog actions

Interpretation:

- recommendations are implemented
- they are not a dead feature
- they are not strongly surfaced as a simple user-facing product concept

V1 decision:

- recommendations are out of v1
- ratings/reviews remain the social signal kept for release

Action:

- hide recommendation UI
- remove recommendation flows from v1 docs and release narrative
- leave backend/data removal as an explicit cleanup decision rather than an accidental partial deletion

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

- course recommendation endpoints in [backend/api/courses.py](/Users/justinmelger/Desktop/github/learning-platform/backend/api/courses.py:74)
- path recommendation endpoints in [backend/api/paths.py](/Users/justinmelger/Desktop/github/learning-platform/backend/api/paths.py:71)
- recommendation services and repositories
- recommendation-derived notifications/activity events

### Frontend

- course card/menu recommend actions
- path card/menu recommend actions
- recommendation summaries shown on cards/detail/home
- “recommended for you” or similar wording in learning/home surfaces

### Docs

- roadmap references to recommendations as a core capability
- architecture docs that describe recommendations as part of the current product contract
- v1 docs and release notes

## 5. Suggested Execution Order

1. Remove recommendation language from v1 docs.
2. Hide recommendation UI from the released frontend.
3. Decide whether backend recommendation APIs remain dormant for now or are removed before release.
4. Clean up stale route/page code.

## 6. Removal Rule

For v1 cleanup:

- remove stale route implementations that are not canonical
- hide or disable implemented-but-cut features from the user-facing app
- only delete deeper backend/data code when the removal is intentional and fully mapped
