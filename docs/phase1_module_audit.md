# Phase 1 Canonical Module Audit

This document records the first canonical module audit from the Phase 1 stabilization checklist.

The purpose is to classify older page/support packages by actual runtime role:

- `keep`
- `move later`
- `remove now`

The goal is to remove ambiguity before deeper cleanup work starts.

## Activity Package

Package:
- `frontend/ui/nicegui/pages/activity/*`

Current role:
- shared activity/feed support layer used by the canonical Teams page
- not a standalone shipped route anymore

Classification:

- `keep`
  - `activity/view_model.py`
    - used by Teams activity/inbox rendering
  - `activity/ui_glue.py`
    - used by Teams and activity tests
  - `activity/sections.py`
    - still provides shared feed rendering
  - `activity/route_init.py`
    - canonical query-tab parsing for Teams initial tab

- `move later`
  - `activity/controller.py`
    - still framed as an `/activity` controller even though the canonical surface is Teams
    - should eventually move to a shared activity support area or become Teams-owned
  - `activity/state.py`
    - still describes an old activity-page state concept rather than a shared feed projection layer

- `remove now`
  - none identified in this pass

Notes:
- the package is not dead, but the package name still reflects pre-refactor history
- this is a good candidate for later consolidation into a shared activity support package

## Home vs Learning

Packages:
- `frontend/ui/nicegui/pages/home/*`
- `frontend/ui/nicegui/pages/learning/*`

Current role:
- `learning/*` owns the canonical `/home` route and the actual Home page implementation
- `home/*` is now mostly a legacy support package for shared stats/profile behavior plus the root redirect binder

Classification:

- `keep`
  - `home/page.py`
    - canonical root redirect to `/home`
  - `home/controller.py`
    - still used by Profile controller aliasing
  - `home/state.py`
    - still used by Profile
  - `home/transitions.py`
    - still used by Profile loading state
  - `home/helpers.py`
    - still used by Profile stats helpers
  - all of `learning/*`
    - canonical Home route implementation

- `move later`
  - `home/controller.py`, `home/state.py`, `home/transitions.py`, `home/helpers.py`
    - these should eventually become Profile/shared-stats-owned modules instead of remaining under `pages/home`

- `remove now`
  - `home/sections.py`
    - no production imports
    - only referenced by its own isolated tests
    - not part of the canonical `/home` implementation anymore

Notes:
- this is the clearest example of a package that is not dead but is legacy-shaped
- future cleanup should either move these helpers to Profile or to a neutral stats/support package

## Courses Package

Package:
- `frontend/ui/nicegui/pages/courses/*`

Current role:
- support package for shared course cards, filters, reducers, controller logic, and detail-dialog compatibility
- still actively used by Explore and Share flows

Classification:

- `keep`
  - `controller.py`
  - `actions.py`
  - `filters.py`
  - `reducers.py`
  - `sections.py`
  - `state.py`
  - `transitions.py`
  - `ui_glue.py`
  - `view_model.py`
  - `media.py`
  - `orchestration.py`
  - `dialogs.py`
  - `detail_flow.py`

- `move later`
  - none identified in this pass

- `remove now`
  - `detail_flow.py`
    - dead dialog-flow compatibility module with no production imports

Notes:
- this package is not dead code
- the route implementation may be gone, but the package remains a real support layer for Explore and Share

## Articles Package

Package:
- `frontend/ui/nicegui/pages/articles/*`

Current role:
- support package for article card rendering, filtering, dialogs, and controller logic
- still used by Explore and Share flows

Classification:

- `keep`
  - `controller.py`
  - `actions.py`
  - `filters.py`
  - `reducers.py`
  - `sections.py`
  - `state.py`
  - `transitions.py`
  - `ui_glue.py`
  - `view_model.py`
  - `dialogs.py`
  - `orchestration.py`

- `move later`
  - none identified in this pass

- `remove now`
  - `detail_flow.py`
    - test-only legacy dialog-flow compatibility module

Notes:
- `detail_flow.py` is the strongest legacy candidate in this package, but it should be removed in a dedicated cleanup slice after confirming no indirect runtime use remains

## Paths Package

Package:
- `frontend/ui/nicegui/pages/paths/*`

Current role:
- active support package for path cards, filters, reducers, controller logic, and detail interactions
- still used directly by Explore and Share

Classification:

- `keep`
  - `controller.py`
  - `actions.py`
  - `filters.py`
  - `filter_flow.py`
  - `reducers.py`
  - `sections.py`
  - `state.py`
  - `transitions.py`
  - `ui_glue.py`
  - `view_model.py`
  - `dialogs.py`
  - `orchestration.py`
  - `detail_flow.py`

- `move later`
  - none identified in this pass

- `remove now`
  - `route_init.py`
    - test-only route-era helper with no production imports
  - `detail_flow.py`
    - test-only dialog-flow compatibility module with no production imports

Notes:
- this package is structurally active and should not be treated as dormant

## Immediate Follow-Up

Safe cleanup actions unlocked by this audit:

1. remove `frontend/ui/nicegui/pages/home/sections.py`
2. remove its isolated tests
3. clean stale “insights” docstrings in `pages/home/*`
4. schedule a later move of `pages/home` stats helpers into Profile/shared-stats ownership
5. remove test-only `articles/detail_flow.py`, `paths/detail_flow.py`, and `courses/paths route_init.py`
6. remove dead `courses/detail_flow.py` and `explore/detail_flow.py` compatibility bridge

## Deferred Follow-Up

These are good next audit targets but not part of this first pass:

- `detail_flow.py` modules in `articles`, `courses`, and `paths`
- `route_init.py` modules in `courses` and `paths`
- deeper Teams/activity support package consolidation
