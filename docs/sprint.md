# Sprint Plan

## Current direction
- Prioritize Phase `11E` IA simplification before remaining Phase `11A` visual polish.
- Complete all open non-user-testing items in Phase `11` before starting Phase `14` user testing/pilot validation work.
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
  - [x] Isolate backend integration test auth/session state to reduce intermittent `401/404/500` failures.
  - [x] Sync `docs/architecture_backend.md` with current course/recommendation/review model + service flow details.

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
