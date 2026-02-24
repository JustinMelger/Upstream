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
  - [ ] Share flow productivity (Courses/Articles): add one-click “apply all suggestions” and per-field “re-suggest” actions.
  - [ ] Share flow safety (Courses/Articles): provide “metadata unavailable” fallback UX with smart placeholders/examples.
- [ ] Complete open `11A.2` catalog polish follow-ups:
  - [ ] Topbar clarity follow-up (Articles): add explicit sort labeling/grouping and separate count metadata from action controls.
  - [ ] Empty-state density polish (Articles): tighten spacing and reduce vertical whitespace while preserving CTA prominence.
  - [ ] Filter rail visual-weight pass (catalog pages): further de-emphasize rail contrast/surface treatment so cards remain dominant.
- [ ] Keep architecture quality gates green during Sprint 4:
  - [ ] `uv run ruff check ...` on touched modules.
  - [ ] `uv run mypy ...` on touched modules.
  - [ ] Targeted `pytest` coverage for newly extracted helpers/orchestration.
