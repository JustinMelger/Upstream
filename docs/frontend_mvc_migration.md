# Frontend MVC Migration Playbook

## Purpose

This playbook defines the practical migration steps for moving NiceGUI pages
to the lightweight MVC pattern documented in `docs/architecture_frontend.md`.

Use this for implementation sequencing and PR-level execution details.

## MVC Migration Template (Short)

Use this checklist when migrating a page to folder-based MVC:

1. Create page folder: `pages/<domain>/page.py` (View), `pages/<domain>/controller.py` (Controller), `pages/<domain>/state.py` (Model state), `pages/<domain>/__init__.py` (exports `register`).
2. Move typed page state dataclasses to `state.py`.
3. Move API/workflow orchestration to `controller.py`.
4. Keep `page.py` focused on UI composition, event binding, and component calls.
5. Extract large UI blocks into `components/*_sections.py`.
6. Add compatibility shim module for old imports during transition.
7. Add/adjust tests: controller orchestration tests, page/helper smoke tests, import/register smoke checks.

## MVC Implementation Plan

Phase 1: Establish pattern baseline (done on `paths`)

- Introduce folder-based page structure: `pages/<domain>/page.py`, `pages/<domain>/controller.py`, `pages/<domain>/state.py`.
- Keep compatibility shims for legacy imports during transition.
- Extract high-churn UI sections into reusable components.

Phase 2: Reduce page size with complementary patterns

- Add ViewModel/presenter mappers for card/detail display data.
- Extract dialog modules (`*_dialog.py`) so page modules stop owning large modal bodies.
- Move event handlers into action modules (`*_actions.py`) where helpful.

Phase 3: Standardize state transitions

- Introduce reducer-style helpers for page state transitions: loading start/success/error, filter/sort/scope changes, optimistic mutation + rollback patterns.
- Keep reducers pure and unit-tested.

Status:
- `paths`: complete
- `courses`: complete (package conversion + route init + state + controller + reducers + view-model + dialogs/actions + detail-flow + transitions + ui-glue + sections extraction complete, including filters/status-control, course-card, empty-state, and pagination UI blocks; architecture tests added)
- `learning`: complete (package conversion + controller/state + actions + route-init + sections + ui-glue extraction complete for core flows; architecture/controller/route-init/glue tests added)
- `articles`: complete (package conversion + controller/state + dialogs/actions + sections/ui-glue + reducers/transitions extraction complete; architecture/controller/action/glue/reducer/transition tests added)
- `home`: complete (package conversion + controller/state + sections/transitions extraction complete; architecture/controller/transition tests added)
- `activity`: complete (package conversion + controller/state + route-init + transitions + ui-glue + sections extraction complete; architecture/controller/route-init/transition/glue tests added)
- `admin_users`: complete (package conversion + controller/state + transitions + sections/ui-glue extraction complete; architecture/controller/transition/glue tests added)
- `ai_curator`: complete (package conversion + controller/state + transitions + ui-glue extraction complete; architecture/controller/transition/glue tests added)
- `login`: complete (package conversion + controller/state + transitions + ui-glue extraction complete; architecture/controller/transition/glue tests added)

Phase 4: Roll out by page priority

1. `paths` (reference implementation; complete and stabilize)
2. `courses` (complete; keep stable as secondary reference)
3. `learning` (complete; keep stable as secondary reference)
4. Smaller pages only as needed

Phase 5: Clean up and enforce (complete)

- Compatibility shim cleanup complete: page package exports are now `register`-only.
- Tests import helper functions from their source modules (for example `pages/*/page.py` or `pages/home/helpers.py`) rather than package re-exports.
- Added enforcement guard in tests to keep package export surface minimal.
- PR checklist: Page = composition/bindings only; Controller = workflow orchestration; Model = typed state + transition helpers; Components = reusable view sections.

## Reference Implementation: Paths

Completed (Phase 1 + Phase 2 + Phase 3):

- Folder-based MVC page package in `pages/paths/`: `page.py`, `controller.py`, `state.py`, `__init__.py`.
- View-model extraction in `pages/paths/view_model.py`: badge/label formatting, path progress/outcomes, detail-dialog presentation mapping, path card display mapping (`map_path_card_view`).
- Dialog extraction in `pages/paths/dialogs.py`: `build_share_path_dialog`, `open_edit_path_dialog`.
- Action extraction in `pages/paths/actions.py`: recommend flow, link copy flow, track/untrack toggle wiring, per-card callback factory (`build_path_card_actions`).
- Detail orchestration extraction in `pages/paths/detail_flow.py`: `open_path_details_dialog`.
- Reducer extraction in `pages/paths/reducers.py`: filter/sort/scope transitions, facet count/options transitions.
- UI glue extraction in `pages/paths/ui_glue.py`: active-filter chip descriptors, pagination transition (`next_visible_count`).
- Route/query init extraction in `pages/paths/route_init.py`: initial scope/path/dialog resolution, intent consume checks.
- Phase 3 transition helpers in `pages/paths/transitions.py`: loading lifecycle transitions, load-error reset transition, optimistic select/unselect + rollback transitions.

Module boundaries (enforced by tests):

- `page.py`: UI composition + event binding only.
- `dialogs.py`, `detail_flow.py`, `actions.py`: UI-facing flow modules, allowed to import `nicegui`.
- `controller.py`: API/workflow orchestration; no `nicegui` imports.
- `state.py`: typed page state models only.
- `reducers.py`, `transitions.py`, `view_model.py`, `ui_glue.py`, `route_init.py`: pure helpers; no `nicegui` imports.
- `page.py` should consume path domain logic via `pages/paths/*` modules (not directly from low-level service modules).

Migration recipe (apply to next page, e.g. `courses`):

1. Create `pages/<domain>/` with `page.py`, `controller.py`, `state.py`, `__init__.py`.
2. Move API calls and multi-step workflows from page into `controller.py`.
3. Move typed mutable page state into `state.py`.
4. Extract pure derivations into `view_model.py` (display mapping) and `reducers.py` (filter/sort/facet transitions).
5. Extract UI modal/detail flows into `dialogs.py` / `detail_flow.py`; extract callback factories into `actions.py`.
6. Extract route/query and small UI glue into dedicated helpers (`route_init.py`, `ui_glue.py`) when page grows.
7. Add boundary tests: pure modules must stay `nicegui`-free; page must import domain logic through page-package modules.
8. Add transition tests: loading lifecycle + optimistic mutation/rollback success/failure behavior.

Next:

- Maintain architecture boundaries and test guardrails as new features are added.
- Add/expand page-level integration tests for critical flows when behavior changes.
