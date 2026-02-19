# Frontend MVC Migration Playbook

## Purpose

This playbook defines the practical migration steps for moving NiceGUI pages
to the lightweight MVC pattern documented in `docs/architecture_frontend.md`.

Use this for implementation sequencing and PR-level execution details.

## MVC Migration Template (Short)

Use this checklist when migrating a page to folder-based MVC:

1. Create page folder:
   - `pages/<domain>/page.py` (View)
   - `pages/<domain>/controller.py` (Controller)
   - `pages/<domain>/state.py` (Model state)
   - `pages/<domain>/__init__.py` (exports `register`)
2. Move typed page state dataclasses to `state.py`.
3. Move API/workflow orchestration to `controller.py`.
4. Keep `page.py` focused on UI composition, event binding, and component calls.
5. Extract large UI blocks into `components/*_sections.py`.
6. Add compatibility shim module for old imports during transition.
7. Add/adjust tests:
   - controller orchestration tests
   - page/helper smoke tests
   - import/register smoke checks

## MVC Implementation Plan

Phase 1: Establish pattern baseline (done on `paths`)

- Introduce folder-based page structure:
  - `pages/<domain>/page.py`
  - `pages/<domain>/controller.py`
  - `pages/<domain>/state.py`
- Keep compatibility shims for legacy imports during transition.
- Extract high-churn UI sections into reusable components.

Phase 2: Reduce page size with complementary patterns

- Add ViewModel/presenter mappers for card/detail display data.
- Extract dialog modules (`*_dialog.py`) so page modules stop owning large modal bodies.
- Move event handlers into action modules (`*_actions.py`) where helpful.

Phase 3: Standardize state transitions

- Introduce reducer-style helpers for page state transitions:
  - loading start/success/error
  - filter/sort/scope changes
  - optimistic mutation + rollback patterns
- Keep reducers pure and unit-tested.

Phase 4: Roll out by page priority

1. `paths` (reference implementation; complete and stabilize)
2. `courses` (largest remaining page)
3. `learning` (next highest orchestration complexity)
4. Smaller pages only as needed

Phase 5: Clean up and enforce

- Remove deprecated compatibility shims after migration windows.
- Add a lightweight checklist to PR reviews:
  - Page = composition/bindings only
  - Controller = workflow orchestration
  - Model = typed state + transition helpers
  - Components = reusable view sections
