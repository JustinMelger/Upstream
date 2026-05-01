# Phase 1 Canonical Module Audit

This document records the first canonical module audit from the Phase 1 stabilization checklist.

The purpose is to classify older page/support packages by actual runtime role:

- `keep`
- `move later`
- `remove now`

The goal is to remove ambiguity before deeper cleanup work starts.

## Activity Package

Packages:
- `frontend/ui/nicegui/pages/activity/*`
- `frontend/ui/nicegui/pages/shared_activity/*`

Current role:
- shared feed support now lives in `frontend/ui/nicegui/pages/shared_activity/*`
- the old `activity/*` package has been fully retired

Classification:

- `keep`
  - `shared_activity/controller.py`
    - canonical feed loader used by shared activity tests/support flows
  - `shared_activity/state.py`
    - canonical feed state model used by shared activity tests/support flows
  - `shared_activity/route_init.py`
    - canonical query-tab parsing for Teams initial tab
  - `shared_activity/view_model.py`
    - canonical typed activity-feed projections used by Teams/tests
  - `shared_activity/ui_glue.py`
    - canonical pure feed-formatting helpers used by Teams/tests
  - `shared_activity/transitions.py`
    - canonical feed-loading transition helpers used by tests
  - `shared_activity/sections.py`
    - canonical shared feed renderer used by activity/teams tests

- `move later`
  - none identified in this pass

- `remove now`
  - `activity/*`
    - fully replaced by `shared_activity/*`

Notes:
- the shared feed subsystem now has one canonical home under `shared_activity/*`

## Home vs Learning

Packages:
- `frontend/ui/nicegui/pages/home/*`
- `frontend/ui/nicegui/pages/learning/*`

Current role:
- `learning/*` owns the canonical `/home` route and the actual Home page implementation
- `home/*` is now the root redirect binder only
- `shared_stats/*` owns the shared stats/profile support helpers

Classification:

- `keep`
  - `home/page.py`
    - canonical root redirect to `/home`
  - `shared_stats/controller.py`
    - shared stats orchestration used by Profile/tests
  - `shared_stats/state.py`
    - shared stats UI state used by Profile/tests
  - `shared_stats/transitions.py`
    - shared stats loading state helpers used by Profile/tests
  - `shared_stats/helpers.py`
    - shared stats helper functions used by Profile/tests
  - all of `learning/*`
    - canonical Home route implementation

- `move later`
  - none identified in this pass

- `remove now`
  - `home/sections.py`
    - no production imports
    - only referenced by its own isolated tests
    - not part of the canonical `/home` implementation anymore

Notes:
- this was the clearest example of a package that was legacy-shaped
- the shared support has now been moved to a neutral stats/support package

## Courses Package

Package:
- `frontend/ui/nicegui/domains/courses/*`

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
- `frontend/ui/nicegui/domains/articles/*`

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
- `frontend/ui/nicegui/domains/paths/*`

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
