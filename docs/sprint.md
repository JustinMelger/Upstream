# Sprint Plan

## Current direction
- Prioritize Phase `11E` IA simplification before remaining Phase `11A` visual polish.
- Complete all open non-user-testing items in Phase `11` before starting Phase `14` user testing/pilot validation work.
- Keep roadmap as strategy/source of truth and use this file for sprint execution tracking.

## Sprint 10 — UX + Style Modernization (Active)
Goal: deliver a coherent, modern visual system and interaction polish across `Home`, `Explore`, and detail surfaces, while finishing first-time clarity gaps.

Timebox:
- [ ] 2 weeks (start next working day)

In scope:
- [ ] `11A.1` Modernization Sprint 1 (typography scale, spacing rhythm, single component language).
- [ ] `11A.4` Motion polish for refreshes/filter state/card updates.
- [ ] `11A.4` Page identity pass (distinct section language + hero treatments).
- [ ] `11E.3` + `11E.7` first-time clarity completion (intro/empty states/next-step clarity consistency).
- [ ] Accessibility style essentials from `11C` that are part of UX polish (focus visibility, icon-label clarity, keyboard/focus behavior in high-traffic controls).
- [ ] Design review + targeted page redesign for high-traffic surfaces (`Home`, `Explore`, and one detail page).

Out of scope:
- [ ] Media pipeline/backend ingestion work (`11A.3` thumbnail fetch/persistence/quality gates).
- [ ] Activity feed v2 behavior expansion (`11B` filters/unread/grouping/pagination).
- [ ] Phase `12+` analytics and AI-curation expansion.

Execution slices:
- [ ] Slice 10.0: design review baseline (audit + decisions)
  - [ ] Run UX/UI audit on `Home`, `Explore`, `Teams`, `Profile`, and detail pages against clarity/hierarchy/consistency criteria.
  - [ ] Capture current-state screenshots and annotate top friction points (scanability, CTA hierarchy, density, visual consistency).
  - [ ] Produce a prioritized redesign list: `must-change now` vs `defer`.
- [ ] Slice 10.1: design tokens + component language baseline
  - [ ] Finalize typography hierarchy and spacing scale in `frontend/ui/nicegui/core/theme.py`.
  - [ ] Normalize card/button/chip/input treatment across `Explore`, `Home`, and detail pages.
  - [ ] Remove remaining visual one-offs that conflict with canonical component styling.
- [ ] Slice 10.2: motion + interaction polish
  - [x] Add 120-200ms transitions for list/filter/sort state changes.
  - [x] Add subtle stagger/enter animations for key card lists.
  - [x] Standardize inline feedback patterns for save/track/select/review actions.
- [ ] Slice 10.3: page identity pass
  - [x] Strengthen page-specific hero language and section framing for `Home` and `Explore`.
  - [x] Keep interaction model unchanged while making each primary page visually distinct.
- [ ] Slice 10.3b: targeted page redesign implementation
  - [x] Redesign `Home` hero + first-scroll section layout for stronger “what to do next” clarity.
  - [x] Redesign `Explore` top section and card-density rhythm for faster scan + action.
  - [x] Redesign one detail page template (`course` preferred) as the new reference pattern.
  - [x] Reuse redesigned template patterns in path/article details where low-risk.
- [x] Slice 10.4: first-time clarity + accessibility polish
  - [x] Complete any remaining onboarding intro and empty-state next-action inconsistencies.
  - [x] Ensure visible focus states and keyboard flow for menus/dropdowns/dialog triggers.
  - [x] Ensure icon-only actions expose clear ARIA labels and visible tooltips/text hints where needed.
- [ ] Slice 10.5: visual quality gate hardening
  - [ ] Commit stable visual baselines and enable strict visual-regression enforcement in CI (`11D` remaining item).
  - [ ] Deferred: explicit user decision on 2026-03-09 to skip strict visual-baseline enforcement for now; keep this item queued.
- [ ] Slice 10.5b: per-file ignore burn-down on active modules
  - [x] Remove stale per-file ignore from `frontend/ui/nicegui/core/errors.py` by tightening exception handling instead of relying on `BLE001`.
  - [x] Audit remaining per-file complexity ignores and remove any that no longer mask real violations.
  - [x] Prioritize strict-scope and active-surface files first (`frontend/ui/nicegui/core/*`, then touched page/section modules).
  - [x] Remove active-module per-file ignores from:
    - [x] `frontend/ui/nicegui/core/errors.py`
    - [x] `frontend/ui/nicegui/pages/learning/sections.py`
    - [x] `frontend/ui/nicegui/pages/profile/page.py`
    - [x] `frontend/ui/nicegui/pages/learning/page.py`
    - [x] `frontend/ui/nicegui/pages/ai_curator/page.py`
    - [x] `frontend/ui/nicegui/pages/admin_users/page.py`
    - [x] `frontend/ui/nicegui/pages/courses/sections.py`
  - [x] Record and execute the next extraction target when a page stays structurally large even after complexity cleanup:
    - [x] Extract `frontend/ui/nicegui/pages/teams/page.py` route-specific UI composition into `frontend/ui/nicegui/pages/teams/page_ui.py` and keep `page.py` as auth guard + route binder + initial load orchestration.
    - [x] Decompose `frontend/ui/nicegui/pages/share/page.py` by flow and responsibility instead of using a single overflow file:
      - [x] separate item-share UI from path-share UI
      - [x] separate control builders from draft wiring and action wiring
      - [x] keep `page.py` focused on route registration, controller setup, and flow selection
- [ ] Slice 10.6: learning-item unification (`video` + `course` + `article`)
  - [x] Naming foundation: use `Learning item` as canonical shared UI term for course/article surfaces.
  - [x] Unified UI mapping: add shared view-model contract with `learning_item_type` (`video`, `article`, `course`, `doc`).
  - [x] Share flow consolidation: merge `/share/course` + `/share/article` into `/share/item` and keep route redirects.
  - [x] Type-tag system: show compact content-type tags (`Video`, `Article`) on cards + detail surfaces.
  - [x] Explore simplification: keep one scalable Learning Items catalog section (no duplicated course/article rails).
  - [x] Copy/IA cleanup: remove mixed wording drift (`Share course` vs `Share article`) across routes and labels.
  - [x] Compatibility + telemetry: preserve old links and add tracking for old-route usage during migration.
- [x] Slice 10.7: learning-item subtype completion
  - [x] Lock the initial subtype taxonomy to `video|course|article` and document `Learning item` as the primary shareable object.
  - [x] Add URL/provider-based subtype detection so YouTube links map to `video`, Udemy links map to `course`, and generic written links map to `article` unless a stronger rule exists.
  - [x] Extend `/share/item` to support explicit subtype selection and auto-detection while preserving compatibility redirects from `/share/course` and `/share/article`.
  - [x] Restore course share validation and field parity on the new share page, especially the required-description behavior.
  - [x] Rework Explore learning-item rendering so available videos, courses, and articles remain visible in the default state rather than being hidden by naive concatenation.
  - [x] Add focused tests for subtype detection, `/share/item` publish behavior, Explore mixed rendering, and compatibility route contracts.

Validation and acceptance criteria:
- [ ] Core pages (`Home`, `Explore`, detail pages) use one consistent typography/spacing/component language.
- [ ] Shared content surfaces use one consistent `Learning item` terminology model without course/article naming drift.
- [ ] Learning-item subtype taxonomy is stable and explicit:
  - [x] YouTube links classify as `video`.
  - [x] Udemy links classify as `course`.
  - [x] Generic written links classify as `article` unless a stronger rule exists.
  - [x] `/share/item` supports explicit subtype selection and successful publish flows for `video`, `course`, and `article`.
  - [x] Explore uses one learning-item model without hiding one available subtype behind another in the default view.
- [ ] Interaction transitions are present, subtle, and consistent (no abrupt state jumps on major list/filter/card updates).
- [ ] First-time clarity goals are measurably improved:
  - [x] no ambiguous empty-state next steps on primary pages.
  - [x] intro/onboarding flow is dismissible and non-blocking.
- [x] Accessibility UX polish passes focused checks for keyboard navigation + visible focus + icon-action labeling on touched surfaces.
- [ ] CI enforces visual snapshots strictly with committed stable baselines.
- [ ] Active-sprint cleanup reduces per-file ignore debt rather than adding or normalizing it.
- [ ] Large route modules continue moving toward thin-binder architecture:
  - [x] `teams/page.py` uses `page_ui.py` when page-local NiceGUI composition becomes the dominant remaining weight.
  - [x] `share/page.py` is reduced by package decomposition, not by shifting one oversized route file into another oversized UI file.
- [ ] Design review output is documented and actionable (before/after evidence + accepted redesign decisions).

Tracking:
- [ ] Update roadmap checkboxes for completed `11A/11C/11D/11E` UX-style items at sprint close.
- [ ] Record before/after screenshots for `Home`, `Explore`, and one detail page variant in CI artifacts.
- [ ] Add a short design-review log section in this file (decision, rationale, affected pages/components).
- [x] Add/maintain focused regression coverage for `/share/item`, subtype detection, and Explore mixed learning-item visibility rather than broad new snapshot churn.

### Sprint 10 Design-Review Log (2026-03-07)
Reference checklist: `docs/ui_system.md`

- Decision: adopt a single SaaS-polish governance checklist for primary pages.
  - Rationale: prevent local visual fixes from diverging into per-page styles.
  - Affected: `Home`, `Explore`, `Profile`, `Teams`, shared `theme.py`.

- Audit snapshot (current):
  - `Home`: mostly pass.
    - Pass: dominant next action, clear hierarchy, strong card language.
    - Partial: occasional title/hero size drift (recently reduced), keep monitoring.
  - `Explore`: mostly pass.
    - Pass: compact card rhythm, single primary per card, improved empty states.
    - Partial: ensure all rails keep identical hover intensity and metadata density.
  - `Profile`: partial -> mostly pass after redesign.
    - Pass: overview + controls + metrics + chart + table structure.
    - Partial: continue segmented-control and table rhythm tuning from visual QA.
  - `Teams`: partial.
    - Pass: card language and empty/error blocks exist.
    - Missing: full section-header/microcopy consistency and stronger first-viewport next-action clarity.

- Must-change-now (remaining in Sprint 10):
  - [x] Teams page hierarchy pass (title/microcopy/action rhythm in first viewport).
  - [x] Cross-page hover/elevation normalization audit (cards + action rows).
  - [x] Empty-state copy consistency pass using one instructional style.

- Defer (post Sprint 10 unless time remains):
  - [ ] Full strict visual-baseline CI enforcement (`11D` final open checkbox).
  - [ ] Extended chart/table interaction features (sorting/filter controls on analytics blocks).

- Decision (2026-03-09): canonicalize share to `/share/item` while keeping explicit type choices at entry points.
  - Rationale: reduce implementation complexity and route sprawl without sacrificing user clarity in “what am I sharing?”
  - Affected: `frontend/ui/nicegui/pages/share/*`, `frontend/ui/nicegui/pages/explore/*`, route/test contracts, terminology copy.

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
- [x] Complete `11E.6` terminology alignment:
  - [x] Canonicalize language for `Track` vs `Save` vs `Select` across cards, dialogs, and filters.
  - [x] Align `Shared` vs `Recommended` semantics in labels and page copy.
  - [x] Add contextual purpose subtitles under primary page titles (`Home`, `Explore`, `Teams`, `Profile`).
  - [x] Finish learning-item unification follow-through: `/share/item` subtype routing, Explore mixed-feed subtype signaling, first-class `video`, and capability-aware copy on Home/Explore/Activity/Teams.
- [ ] Complete `11E.7` first-time user clarity pass:
  - [x] Add dismissible 3-step first-login intro.
  - [x] Ensure each key empty state has exactly one primary action.
  - [x] Ensure no primary page loads without an unambiguous next step.
  - [ ] Concrete `11E.7` acceptance slices:
    - [ ] Audit `Home`, `Explore`, `Teams`, and `Profile` empty states against the current IA and keep one obvious next step per page.
    - [ ] Recheck onboarding copy and hints against canonical routes (`/home`, `/explore`, `/teams`, `/share/item`, `/share/path`) and remove stale wording.
    - [ ] Verify no-team and no-content states clearly route users to `Teams` and `Explore` without mixed team/share terminology.
    - [ ] Add focused integration coverage for “one clear next action” on key first-use empty states.
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
  - [x] Explore parity follow-up: align path/article cards to the accepted course-card slot rhythm and baseline alignment in Explore.


## Sprint 5 — Hardening + Phase 11 Readiness (Non-UX)
- [ ] Stabilize quality gates and type discipline:
  - [x] Resolve current `mypy` baseline errors in `frontend/ui/nicegui/pages/paths/*` and `frontend/ui/nicegui/pages/explore/page.py`.
  - [ ] Keep `ruff` and `mypy` green on touched modules for every sprint slice.
  - [x] Add/update targeted tests for any extracted orchestration/controller helpers.
  - [x] Lint ratchet near-term target for non-legacy modules:
    - [x] `mccabe<=25`
    - [x] `max-branches<=20`
    - [x] `max-statements<=100`
    - [x] `max-args<=10`
    - [x] `max-returns<=8`
  - [x] Define enforcement tiers in `pyproject.toml` (strict in `services/controllers/orchestration/reducers`, slightly looser in UI composition modules).
  - [x] Remove temporary per-file complexity ignores from active modules by extracting long/high-branch functions.
  - [x] Reduce argument-heavy APIs (`PLR0913`) using typed payload/context objects (dataclass/view-model based).
  - [x] Add architecture regression guard for complexity in active page modules (prevent new regressions).
  - [x] Keep legacy-page excludes fixed (no broadened ignore scope).
  - [x] Roll out CI ratchet mode: fail on new violations first, then enforce full thresholds.
  - [ ] Complete open Phase `11D` engineering items:
    - [ ] Add visual regression/smoke e2e checks for critical flows (`login`, `track`, `review`, `select path`).
      - [x] Phase slice: add Playwright smoke coverage for `login` + `track` and upload screenshots/log artifacts in CI.
      - [x] Phase slice: add `review` + `select path` smoke coverage.
      - [x] Phase slice: add visual-regression snapshot assertion harness + baseline update workflow.
      - [ ] Phase slice: commit stable baseline images and enable strict visual-regression enforcement in CI.
    - [ ] Concrete `11D` close-out slices:
      - [x] Keep the ratchet + strict-core CI script aligned with the workflow entrypoint (`scripts/lint_quality_gate.sh` + `.github/workflows/ci.yml`) and remove shell-flow bugs that can hide real failures.
      - [x] Fix active strict-core regressions exposed by the quality gate in `backend/services`, `frontend/ui/nicegui/core`, and `frontend/ui/nicegui/services`.
      - [ ] Commit stable visual baseline images for the existing smoke/visual flows.
      - [ ] Enable strict visual snapshot enforcement in CI once baselines are committed and stable.
      - [ ] Decide and document the E2E environment contract: fail on true regressions, skip only when the external/browser environment is unavailable.

## Sprint 11 — Social Learning Hub v1 (Teams + Scoped Sharing)
- [ ] Align execution to roadmap `Phase 11F`.

- [ ] Slice 11.0: UX flow baseline (no-team and first-team activation)
  - [ ] `/teams` empty state: primary `Create team` action and optional `Join team` secondary action.
  - [ ] `Home` no-team social placeholders: low-noise cards with clear CTA to `/teams`.
  - [ ] Post-create activation: auto-open team detail with add-member/share-first prompts.

- [ ] Slice 11.1: share audience model (API + persistence)
  - [ ] Add audience scope to shares (`public`, `my_teams`, `selected_teams`).
  - [ ] Add team-target persistence model for selected-team shares.
  - [ ] Add backend filtering so visibility matches selected scope.

- [ ] Slice 11.2: Explore share dialog audience selector
  - [ ] Add audience selector to share flows.
  - [ ] Add team multi-select UI when `selected_teams` is chosen.
  - [ ] Add concise “who can see this” helper copy and confirmation context.

- [ ] Slice 11.3: Home + Teams + Shared-tab semantic alignment
  - [ ] Add consistent audience badges on shared items.
  - [ ] Ensure social modules on Home reflect team-scoped relevance.
  - [ ] Align Shared tab wording and visuals to same scope semantics.

- [ ] Slice 11.4: team review-request loop (v1.1)
  - [ ] Add backend `review_requests` schema + migration + API endpoints.
  - [ ] Add `Request review` action on team-scoped shared items.
  - [ ] Add “Conversations needing you” integration from open review requests.
  - [ ] Add completion/dismiss/cancel request flows.

- [ ] Slice 11.5: conversational course discussions (v1.2)
  - [ ] Add backend discussion thread/message schema + migration.
  - [ ] Add discussion API endpoints for create/list/reply/resolve/reopen.
  - [ ] Add frontend discussion entry point (`Discuss`) on course surfaces.
  - [ ] Add compact thread timeline view in course detail.
  - [ ] Integrate open mentions/replies into “Conversations needing you.”

- [ ] Slice 11.6: tests and quality gates
  - [ ] API tests for audience scope and visibility enforcement.
  - [ ] API tests for review-request permissions and lifecycle.
  - [ ] API tests for discussion thread/message lifecycle and permissions.
  - [ ] Frontend integration tests for no-team and first-team flows.
  - [ ] Frontend integration tests for review-request UX states.
  - [ ] Frontend integration tests for discussion thread UX states.
  - [ ] Keep `ruff` and scoped `mypy` green for all touched modules.

- [ ] Exit criteria
  - [ ] New user can create/join a team in under 60 seconds (instrumented).
  - [ ] Visibility model is explicit in UI (no ambiguity about share audience).
  - [ ] No regression for users who only use solo learning/discovery.
  - [x] Isolate backend integration test auth/session state to reduce intermittent `401/404/500` failures.
  - [x] Sync `docs/architecture_backend.md` with current course/recommendation/review model + service flow details.

## Sprint 12 — Open Items Timebox (Phase 11 Closure, Queued)
Goal: close the highest-value open roadmap items in Phase `11` with a strict timebox and ship-ready quality gates.

Dependency:
- [ ] Start only after Sprint 10 exit criteria are fully completed.
- [ ] Keep Sprint 12 in queued state while Sprint 10 is active.

Timebox:
- [ ] 2 weeks

Scope priorities:
- [ ] P0: `11F` collaboration model and UX flow baseline (`11.0` through `11.3` slices from Sprint 11).
- [ ] P1: `11D` strict visual baseline enforcement in CI.
- [ ] P1: `11E` remaining open clarity/consistency acceptance checks.
- [ ] P2: `11F` v1.1/v1.2 collaboration expansion (`review_requests`, threaded discussions) if P0/P1 complete early.

Execution slices:
- [ ] Slice 12.0: open-item lock and sequencing
  - [ ] Freeze active open-item list from `docs/roadmap.md` (Phase `11` only).
  - [ ] Tag each item as `must-close-now` vs `defer`.
  - [ ] Map each `must-close-now` item to an owning sprint slice and test gate.
- [ ] Slice 12.1: teams + no-team activation UX
  - [ ] `/teams` empty state with `Create team` primary CTA and `Join team` secondary path.
  - [ ] `Home` no-team social placeholder with direct CTA to `/teams`.
  - [ ] Post-create activation flow with add-member/share-first prompts.
- [ ] Slice 12.2: audience scoping and visibility semantics
  - [ ] Share audience scope (`public`, `my_teams`, `selected_teams`) in API + persistence.
  - [ ] Explore share dialog audience selector + team multi-select.
  - [ ] Audience badges and wording alignment across `Home`, `Teams`, and `Shared` surfaces.
- [ ] Slice 12.3: CI quality gate completion
  - [ ] Commit stable visual snapshots.
  - [ ] Enable strict visual-regression enforcement in pipeline.
  - [ ] Keep `ruff` primary style gate green on all touched modules.
- [ ] Slice 12.4: optional collaboration expansion (only if capacity remains)
  - [ ] Review-request loop (`review_requests` model/API/UX).
  - [ ] Threaded course discussion baseline (model/API/UX entrypoint).

Acceptance criteria:
- [ ] Highest-priority Phase `11` open items are reduced with no regression in solo learning flows.
- [ ] Team onboarding path is clear for users with zero teams (create/join in under 60s target, instrumented).
- [ ] Share visibility semantics are explicit and consistent across primary pages.
- [ ] CI runs with strict visual baseline enforcement and passes required gates (`ruff`, scoped `mypy`, tests).

Tracking:
- [ ] Update `docs/roadmap.md` checkboxes for each closed item during the sprint.
- [ ] Record sprint-end delta: `Phase 11 open before` vs `Phase 11 open after`.

## Sprint 13 — Paths As Ordered Learning Items (Queued)
Goal: move paths from ordered courses to ordered learning items so `/share/path`, path details, and path editing support `course|video|article` without regressing the current clean architecture boundaries.

Dependency:
- [ ] Start after the current path share/detail route-first model remains stable under targeted regression coverage.
- [ ] Keep phase-1 progress semantics explicit: course tracking continues to drive path progress until generic learning-item completion exists.

Timebox:
- [ ] 2 weeks

Scope priorities:
- [ ] P0: backend path model migration from course-only membership to ordered typed items.
- [ ] P0: frontend `/share/path` and path detail support for mixed learning items.
- [ ] P1: cross-surface cleanup so path summaries and copy say `learning items`, not `courses`, where the model is mixed.
- [ ] P1: docs/tests/architecture guard updates for the new contract.
- [ ] P2: generic learning-item completion for paths is explicitly deferred.

Execution slices:
- [ ] Slice 13.0: path data model + migration
  - [ ] Add backend `path_items` persistence with `path_id`, `item_type`, `item_id`, and `position`.
  - [ ] Migrate existing path-course membership into `item_type="course"` rows.
  - [ ] Keep service/repository code aligned to complexity thresholds by extracting parse/validation helpers instead of adding inline branching.
- [ ] Slice 13.1: path API + service contract
  - [ ] Replace course-only path mutation payloads with ordered typed items.
  - [ ] Validate `course|video|article` references against the correct backing domain before persistence.
  - [ ] Return ordered typed items from path detail/list payloads instead of course-only membership shapes.
- [ ] Slice 13.2: `/share/path` and edit-path UX
  - [ ] Replace course-only selectors with mixed learning-item selection and ordering.
  - [ ] Label the composition field as `Learning items in order`.
  - [ ] Show subtype chips and concise source metadata in the picker so mixed-item selection stays scannable.
- [ ] Slice 13.3: path detail rendering
  - [ ] Render mixed path sequences with visible subtype chips and correct deep-link navigation per item type.
  - [ ] Update path summary copy to reflect `learning items` rather than `courses`.
  - [ ] Keep the routed path detail page as the canonical experience; do not reintroduce hover/dialog-first behavior.
- [ ] Slice 13.4: progress semantics and compatibility
  - [ ] Preserve current course-based progress as the explicit phase-1 rule for mixed paths.
  - [ ] Make videos/articles visible steps in the path without implying unsupported completion tracking.
  - [ ] Add compatibility handling for legacy course-only paths during the migration window.
- [ ] Slice 13.5: tests, docs, and architecture guards
  - [ ] Add backend tests for mixed-item path create/update/detail and migration behavior.
  - [ ] Add frontend tests for `/share/path`, mixed path detail rendering, and deep-link routing for course/video/article items.
  - [ ] Update roadmap/architecture docs and keep route/service-boundary guard tests in sync.

Acceptance criteria:
- [ ] A path can contain ordered `course`, `video`, and `article` items through the canonical `/share/path` flow.
- [ ] Existing course-only paths migrate cleanly with no broken detail pages or edit flows.
- [ ] Path detail pages render mixed sequences and open the correct subtype detail route for each item.
- [ ] Phase-1 progress semantics are explicit and truthful: course tracking still drives progress; videos/articles do not fake completion state.
- [ ] Touched modules remain within the existing clean-code/complexity guardrails (`ruff`, scoped `mypy`, architecture tests, focused regression tests).

Tracking:
- [ ] Update `docs/roadmap.md` to mark the path model as ordered learning items once persistence and UI contracts are implemented.
- [ ] Record the migration contract in `docs/architecture_frontend.md` and `docs/architecture_backend.md`.
- [ ] Keep a short implementation log here if phase-1 scope cuts change (especially progress semantics).

## Sprint TBD — Phase 14 User Testing + Pilot Validation
- [ ] Run 5 first-time-user usability tests and log confusion points.
- [ ] Fix top 5 confusion points before pilot launch.
- [ ] Add pilot observer confusion-log template + triage rubric.
- [ ] Validate first-session navigation clarity and capture outcome metrics.

## Sprint 6 — Roadmap Open-Items Closure (UX-first)
- [ ] Close remaining open `11E` first-use clarity and navigation consistency items:
  - [x] `11E.4`: replace dialog-first Explore detail behavior with dedicated detail routes (`course/path/article`).
  - [x] `11E.4`: convert `/courses`, `/paths`, `/articles` into thin compatibility/deep-link routes and finalize redirect/deprecation plan.
  - [x] `11E.6`: finish cross-page terminology consistency across cards + detail dialogs.
  - [x] `11E.6`: make subtype capability differences explicit so shared surfaces stop treating every learning item like a course (`course`: tracking/recommendations/reviews, `article`: reviews, `video`: lightweight share/detail).
- [ ] Close highest-impact open `11A` visual-system modernization items:
  - [ ] `11A.1`: Modernization Sprint 1 (typography scale + spacing rhythm + unified component language).
  - [ ] `11A.4`: complete page-identity pass (distinct but consistent section language + hero treatments).
  - [ ] `11A.4`: add motion polish for refresh/filter/card-state transitions.
  - [ ] `11A.4`: Modernization Sprint 2 (cohesive 120-200ms motion system + inline feedback).
  - [ ] `11A.4`: Modernization Sprint 3 (surface/depth refinement + social-signal emphasis + accessibility/focus polish).
- [ ] Close open `11A.3` media pipeline durability items:
  - [ ] Extend thumbnail resolution beyond YouTube (provider/oEmbed first, metadata fallback) with caching + SSRF-safe fetch constraints.
  - [ ] Persist URL metadata on create/update (`preview_image_url`, source fields, canonical URL, `metadata_fetched_at`) and add manual refresh.
  - [ ] Add thumbnail quality gate (reject blurry/low-quality images) + fallback policy to branded default image.
  - [ ] Finish media placement alignment polish for card-control and content baselines.
- [ ] Close open `11D` quality-gate item:
  - [ ] Commit stable visual-regression baseline images and enable strict visual-regression enforcement in CI.
- [ ] Start `11B` activity-feed UX v2 foundation (first vertical slice):
  - [ ] Add filters (`All`, `Recommendations`, `Ratings`, `Courses`, `Paths`, `Articles`).
  - [ ] Add pagination/`Load more` and relative timestamps with absolute hover.
  - [ ] Add activity sort correctness (timezone-aware datetime parsing) + malformed-row resilience.
- [ ] Start `11C` reliability/accessibility essentials (phase-11 minimum slice):
  - [ ] Add keyboard/focus fixes for menus/dropdowns/dialogs/card actions.
  - [ ] Add ARIA + icon-action labeling + contrast/focus visibility audit fixes.
  - [ ] Add network/offline banner + retry affordances + standardized section-level error states.

Sprint 6 acceptance criteria:
- [ ] Open roadmap count reduced for Phase `11A/11D/11E` with no regressions in existing architecture/lint/type gates.
- [ ] CI includes strict visual baseline enforcement and remains green on required gates.

## Sprint 7 — Remove Legacy Catalog Surfaces
- [ ] Remove remaining legacy discovery entrypoints while preserving link compatibility:
  - [x] Keep `/courses`, `/paths`, `/articles` as redirect-only compatibility shims (no discovery rendering).
  - [x] Preserve deep-link behavior to Explore detail routes for course/path/article IDs.
  - [x] Keep compatibility for old share URLs until Explore-native share flow fully replaces them.
- [ ] Move remaining management affordances into Explore-native routes:
  - [x] Ensure create/share flows for course/path/article are reachable from Explore without legacy route dependency.
  - [x] Ensure edit/delete/recommend/review management is reachable from Explore detail pages.
  - [x] Remove dependency on `?share=1` fallback once Explore-native share management is complete.
- [ ] Retire legacy dialog-first detail behavior:
  - [x] Remove query-driven legacy detail-open behavior from compatibility pages.
  - [x] Keep dedicated Explore detail routes (`/explore/courses/{id}`, `/explore/paths/{id}`, `/explore/articles/{id}`) as the only detail entry model.
- [ ] Update routing and navigation helpers to Explore-first links:
  - [x] Replace remaining `/courses?...`, `/paths?...`, `/articles?...` deep-link builders with Explore route builders where appropriate.
  - [x] Update activity/notification open-target links to Explore detail routes.
- [ ] Add regression guards for legacy removal:
  - [x] Tests asserting legacy routes are redirect shims and do not render discovery UI.
  - [x] Architecture guard preventing reintroduction of discovery rendering into compatibility routes.
  - [x] Terminology/route contract tests updated for Explore-first model.

Sprint 7 acceptance criteria:
- [x] No user-facing discovery flow requires `/courses`, `/paths`, or `/articles`.
- [x] Legacy links continue to resolve correctly via redirects.
- [x] Full frontend lint/tests pass with no new architecture guard violations.

## Sprint 8 — Remove Legacy Theme + Pages
- [x] Remove legacy route aliases and compatibility endpoints:
  - [x] Remove `/learning` alias from `frontend/ui/nicegui/pages/learning/page.py` (keep `/home` only).
  - [x] Remove `/activity` alias from `frontend/ui/nicegui/pages/activity/page.py` (keep `/teams` only).
  - [x] Remove `/insights` redirect route from `frontend/ui/nicegui/pages/home/page.py`.
  - [x] Remove compatibility routes `/courses`, `/paths`, `/articles` and delete:
    - [x] `frontend/ui/nicegui/pages/courses/compat.py`
    - [x] `frontend/ui/nicegui/pages/paths/compat.py`
    - [x] `frontend/ui/nicegui/pages/articles/compat.py`
- [x] Remove legacy navigation/query compatibility behavior:
  - [x] Delete `?share=1` compatibility checks from legacy compatibility routes after Explore-native share flow is confirmed stable.
  - [x] Remove obsolete route/query init helpers tied to legacy entry model where no longer used.
- [x] Remove legacy theme branches and simplify theme system:
  - [x] Remove `feature_explore_cinema`-specific layout/theme branches from:
    - [x] `frontend/ui/nicegui/components/layout.py`
    - [x] `frontend/ui/nicegui/pages/explore/page.py`
    - [x] `frontend/ui/nicegui/core/theme.py`
  - [x] Keep one canonical visual system for Explore.
  - [x] Remove unused catalog-variant CSS selectors that no longer have route-level consumers.
- [x] Strengthen architecture and route guards:
  - [x] Update route-contract tests to assert only canonical routes are registered.
  - [x] Add guard test preventing reintroduction of deprecated aliases/routes (`/learning`, `/activity`, `/insights`, `/courses`, `/paths`, `/articles`).
  - [x] Keep guard preventing page-level navigation to legacy discovery paths.
- [x] Docs and roadmap cleanup:
  - [x] Update `docs/architecture_frontend.md` route map to canonical-only model.
  - [x] Update `docs/roadmap.md` and `docs/sprint.md` to mark legacy-route/theme removal completion.

Sprint 8 acceptance criteria:
- [x] No legacy aliases/compat routes are registered at runtime.
- [x] No page or helper emits navigation to deprecated legacy routes.
- [x] Theme has no deprecated branch selectors for removed variants.
- [x] Frontend lint + architecture + targeted route/compat tests pass.

## Sprint 9 — Architecture Hardening (Clean Code)
- [x] Enforce clean layering and ownership boundaries:
  - [x] `9.1` Remove service-to-page dependency in AI Curator flow (move transforms to service/core scope).
  - [x] `9.2` Add architecture guard preventing `frontend/ui/nicegui/services/*` importing `frontend/ui/nicegui/pages/*`.
  - [x] `9.3` Reduce Explore cross-page controller coupling via Explore-local facade/gateway.
- [x] Improve reuse and reduce duplication:
  - [x] `9.4` Consolidate duplicated review upsert flow across course/path/article review services.
- [x] Continue complexity extraction on high-change UI modules:
  - [x] `9.5` Extract hotspots in `components/path_card.py`, `components/reviews_panel.py`, `pages/explore/detail_page.py`, `pages/explore/list_sections.py`.
- [x] Docs + guard alignment:
  - [x] `9.6` Update architecture docs/checklists with explicit service/page dependency rule and enforcement notes.

Sprint 9 acceptance criteria:
- [x] No frontend service module imports page-layer modules.
- [x] Architecture guard fails on service->page imports and passes on current tree.
- [x] Explore controller responsibility is reduced (fewer cross-page controller dependencies).
- [x] Duplicated review upsert control flow is reduced without behavior regressions.
