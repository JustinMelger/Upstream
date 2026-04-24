# Phase 1 Stabilization Checklist

This checklist turns Phase 1 of the post-v1 architecture improvement plan into concrete cleanup work.

Phase 1 is intentionally narrow:

- remove legacy residue
- simplify stale helper APIs
- clean naming drift
- remove dead code and obsolete docs/comments
- avoid broad behavior changes unless the cleanup is clearly safe

This is not a feature phase and not a rewrite phase.

## Exit Criteria

Phase 1 is complete when:

- the main production tree no longer carries obvious stale helper signatures or legacy route residue
- page/package APIs match the shipped v1 product model more closely
- dead/duplicate modules are removed or explicitly deferred
- naming and docs no longer reflect removed product concepts
- each cleanup slice is verified with focused lint/tests

## P0: Safe High-Value Cleanup

These items are the first cleanup passes because they reduce confusion without changing the product model.

### 1. Canonical Module Audit

- [x] Review `frontend/ui/nicegui/pages/activity/*` and mark each module as:
  - keep
  - move later
  - remove now
- [x] Review `frontend/ui/nicegui/pages/home/*` for overlap with `pages/learning/*`
- [x] Review `frontend/ui/nicegui/pages/courses/*`, `articles/*`, and `paths/*` for helper modules that still exist only because of earlier routing/layout splits
- [x] Record decisions in a follow-up cleanup note:
  - `docs/phase1_module_audit.md`

### 2. Legacy Naming Cleanup

- [ ] Remove docstrings/comments that still describe removed routes or old page names
- [ ] Rename helper functions/files whose names still reflect removed product concepts
- [ ] Standardize activity-related naming so `Teams`, `Inbox`, `activity`, and `Profile` use the same language model
- [ ] Remove remaining wording/code comments that imply recommendation-first or private-team visibility behavior

### 3. Stale Helper Signature Cleanup

- [ ] Review production helpers with broad callback bundles and trim signatures to the inputs they actually use
- [x] Remove page-local wrappers that no longer add behavior beyond forwarding one call
- [x] Simplify section helper APIs that still accept `on_refresh`, `on_browse_*`, or state parameters only because of older generic contracts
- [ ] Prefer explicit typed dependency dataclasses where a render helper still needs many real inputs

### 4. Dead Import / Dead Wrapper Sweep

- [x] Remove unused imports and leftover one-line wrappers in `frontend/ui/nicegui/pages/*`
- [ ] Remove obsolete formatting/parsing helpers where the logic now lives in `core/*` or `services/*`
- [ ] Remove stale backend support helpers if they only exist for deleted API surface

## P1: Module-By-Module Cleanup

These are still Phase 1 items, but they should happen after the low-risk cleanup passes above.

### Teams / Activity

- [ ] Audit `frontend/ui/nicegui/pages/teams/*` for render/orchestration helpers that can be simplified without changing behavior
- [ ] Audit shared activity helpers used by Teams, Home, and Profile
- [ ] Remove residual “old activity page” concepts from module names or comments where the code is now Teams-owned
- [ ] Confirm there is one clear canonical flow for:
  - inbox rendering
  - team activity rendering
  - team member mutation refresh

### Home / Learning

- [ ] Audit `frontend/ui/nicegui/pages/learning/*` for redesign residue:
  - unused context fields
  - overly generic section contracts
  - duplicate empty-state helpers
- [ ] Remove helpers that still reflect earlier dashboard layouts if they are no longer needed
- [ ] Normalize section naming around `next focus`, `next actions`, `tracked courses`, `selected path`, `team activity`

### Profile

- [ ] Audit `frontend/ui/nicegui/pages/profile/*` for stale summary/overview helpers left behind by the recent page cleanup
- [ ] Remove any chart/table wrappers that no longer carry meaningful behavior
- [ ] Align stats-related naming with the Home/Teams/Profile activity model

### Explore / Detail Surfaces

- [ ] Audit `frontend/ui/nicegui/pages/explore/*` for leftover route-era residue:
  - stale helper names
  - duplicated detail-page support logic
  - obsolete list-flow wrappers
- [ ] Remove helpers that only survive because of earlier dialog/detail transitions
- [ ] Confirm detail-page common helpers are the canonical place for breadcrumb/back-link behavior

### Share

- [ ] Audit `frontend/ui/nicegui/pages/share/*` for draft/publish helpers that still assume broader product scope than v1 supports
- [ ] Remove stale wording helpers or fallback code for removed recommendation concepts
- [ ] Confirm one canonical publish path for:
  - learning items
  - paths

### Backend API Surface

- [ ] Review router docstrings and comments for wording drift from the shipped v1 model
- [ ] Remove obsolete router/service helpers left behind by removed recommendation endpoints
- [ ] Standardize intentionally unused auth-gating parameters and handler naming patterns
- [ ] Audit policy/dependency helpers for duplicates introduced during v1 stabilization

## P2: Cleanup Backlog For After Phase 1

These should stay out of Phase 1 unless they become trivial while touching the area.

- [ ] deeper controller/service reshapes
- [ ] shared detail-page architecture extraction
- [ ] major activity-domain restructuring
- [ ] typed model expansion across older `dict[str, Any]` boundaries
- [ ] large test refactors purely for style

## Working Rules

For every Phase 1 cleanup change:

- [ ] keep the user-facing behavior stable unless the cleanup clearly fixes a bug
- [ ] update docs/comments if the cleanup changes the canonical story of a module
- [ ] run focused `ruff` and `pytest` coverage for the touched area
- [ ] prefer deleting stale code over abstracting around it
- [ ] do not mix broad feature work into the same change

## Suggested Execution Order

1. Canonical module audit
2. legacy naming/doc cleanup
3. stale helper signature cleanup
4. dead wrapper/import sweep
5. Teams/activity cleanup
6. Home/Profile cleanup
7. Explore/detail cleanup
8. backend API wording/helper cleanup
