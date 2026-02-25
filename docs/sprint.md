# Sprint Plan

## Current direction
- Prioritize Phase `11E` IA simplification before remaining Phase `11A` visual polish.
- Keep roadmap as strategy/source of truth and use this file for sprint execution tracking.

## Sprint 1 — IA foundation (11E-first)
- [x] Complete `11E.0` instrumentation baseline for first-action and nav/search events.
- [x] Complete `11E.1` top-level navigation simplification (`Home`, `Explore`, `Teams`, `Profile`) + legacy redirects.
- [x] Start `11E.2` by merging `My learning` + `Insights` into `Home` and relocating full stats to `Profile > Stats`.
- [x] Ship architecture/test/doc sync for new routes and nav:
  - [x] `tests/frontend/ui/nicegui/test_routes.py`
  - [x] `tests/frontend/ui/nicegui/core/test_core_navigation.py`
  - [x] `tests/frontend/ui/nicegui/test_architecture_docs_contracts.py`
  - [x] `docs/architecture_frontend.md`

## Sprint 2 — Discovery + density + targeted 11A follow-up
- [x] Complete `11E.2` Explore consolidation (tabs: `All`, `Courses`, `Paths`, `Articles`) and remove duplicate discovery sections.
- [x] Complete `11E.3` and `11E.4` so `Home` has one dominant next action and `Explore` is search-dominant.
- [x] Complete `11E.5` action-density constraints (one primary CTA + one state control per card).
- [x] Add a unified `Share` entry point in `Explore` (course/path/article chooser) and de-emphasize duplicate share CTAs on deep-link pages.
- [x] Resume highest-impact open `11A` items only after IA settles:
  - [x] `11A.2` Card consistency pass.
  - [x] `11A.2` Action hierarchy pass.
  - [x] `11A.2` Topbar clarity pass.

## Sprint 3 — Terminology + First-Time Clarity + Share-Flow UX
- [ ] Complete `11E.6` terminology alignment:
  - [x] Canonicalize language for `Track` vs `Save` vs `Select` across cards, dialogs, and filters.
  - [x] Align `Shared` vs `Recommended` semantics in labels and page copy.
  - [x] Add contextual purpose subtitles under primary page titles (`Home`, `Explore`, `Teams`, `Profile`).
- [ ] Complete `11E.7` first-time user clarity pass:
  - [x] Add dismissible 3-step first-login intro.
  - [x] Ensure each key empty state has exactly one primary action.
  - [x] Ensure no primary page loads without an unambiguous next step.
  - [ ] Run 5 usability tests and log confusion points; fix top 5 before pilot.
  - [ ] Deferred: execute this item during pilot rollout with a small live user group.
- [ ] Complete open Share-flow UX actions from `11A.3`:
  - [x] Trigger URL metadata suggestion on paste/blur with debounce (keep manual suggest button).
  - [x] Add inline “suggested vs edited” indicators for autofilled fields.
  - [x] Add live URL validation + duplicate hints pre-submit.
  - [x] Add post-submit success summary with quick follow-up actions.

## Sprint 4 — Share Reliability + Catalog Polish
- [ ] Complete highest-impact open `11A.3` reliability/productivity items:
  - [x] Share flow reliability (Courses/Articles): persist unsent draft form state with autosave + recovery after refresh/navigation and explicit “discard draft” action.
  - [x] Share flow productivity (Courses/Articles): add one-click “apply all suggestions” and per-field “re-suggest” actions.
  - [x] Share flow safety (Courses/Articles): provide “metadata unavailable” fallback UX with smart placeholders/examples.
- [ ] Complete open `11A.2` catalog polish follow-ups:
  - [x] Topbar clarity follow-up (Articles): add explicit sort labeling/grouping and separate count metadata from action controls.
  - [x] Empty-state density polish (Articles): tighten spacing and reduce vertical whitespace while preserving CTA prominence.
  - [x] Filter rail visual-weight pass (catalog pages): further de-emphasize rail contrast/surface treatment so cards remain dominant.
  - [x] Explore course-card UX baseline: finalize accepted course-card look/feel and CTA behavior in Explore.
  - [ ] Explore parity follow-up: align path/article cards to the accepted course-card slot rhythm and baseline alignment in Explore.


## Sprint 5 — Hardening + Pilot Readiness (Non-UX)
- [ ] Stabilize quality gates and type discipline:
  - [ ] Resolve current `mypy` baseline errors in `frontend/ui/nicegui/pages/paths/*` and `frontend/ui/nicegui/pages/explore/page.py`.
  - [ ] Keep `ruff` and `mypy` green on touched modules for every sprint slice.
  - [ ] Add/update targeted tests for any extracted orchestration/controller helpers.
  - [ ] Lint ratchet near-term target for non-legacy modules:
    - [ ] `mccabe<=25`
    - [ ] `max-branches<=20`
    - [ ] `max-statements<=100`
    - [ ] `max-args<=10`
    - [ ] `max-returns<=8`
  - [ ] Define enforcement tiers in `pyproject.toml` (strict in `services/controllers/orchestration/reducers`, slightly looser in UI composition modules).
  - [ ] Remove temporary per-file complexity ignores from active modules by extracting long/high-branch functions.
  - [ ] Reduce argument-heavy APIs (`PLR0913`) using typed payload/context objects (dataclass/view-model based).
  - [ ] Add architecture regression guard for complexity in active page modules (prevent new regressions).
  - [ ] Keep legacy-page excludes fixed (no broadened ignore scope).
  - [ ] Roll out CI ratchet mode: fail on new violations first, then enforce full thresholds.
- [ ] Complete open Phase `11D` engineering items:
  - [ ] Add visual regression/smoke e2e checks for critical flows (`login`, `track`, `review`, `select path`).
  - [ ] Isolate backend integration test auth/session state to reduce intermittent `401/404/500` failures.
  - [ ] Sync `docs/architecture_backend.md` with current course/recommendation/review model + service flow details.

## Sprint TBD — Pilot Validation (Planned Later)
- [ ] Run 5 first-time-user usability tests and log confusion points.
- [ ] Fix top 5 confusion points before pilot launch.
- [ ] Add pilot observer confusion-log template + triage rubric.
