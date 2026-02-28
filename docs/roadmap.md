# Roadmap

## Phase 1 — MVP catalog
- [x] Stable data model for courses.
- [x] Search + filter UI.
- [x] One-click course links.
- [x] Basic “Add course” form for curators.

## Phase 2 — Management + paths
- [x] Edit/delete courses.
- [x] Learning paths with ordered sequences.
- [x] Path overview page with progress per path.

## Phase 3 — Auth v1 (self-hosted + optional OAuth)
- [x] API routes: `/auth/login`, `/auth/me`, `/auth/logout`, `/auth/role`, and admin user management under `/auth/users`.
- [x] Session storage: server-side sessions keyed by `X-Session-Token` (frontend stores token in a cookie).
- [x] Bootstrap admin: first login can create the initial admin when no users exist (env-controlled).
- [x] UI: login screen + guarded pages.

## Phase 3b — Auth enhancements (optional)
- [ ] Invite-code login (email + code).
- [ ] OAuth configuration (Google/Microsoft/Okta) via env vars.
- [ ] Admin allowlist (post-auth).

## Phase 4 — Postgres + Async SQLAlchemy + Alembic
- [x] Add Postgres to `docker-compose.yml` and `docker-compose.watch.yml`; standardize on `DATABASE_URL`.
- [x] Add async SQLAlchemy session-per-request scaffolding (`backend/database/session.py`).
- [x] Add Alembic (`alembic/`, `alembic.ini`) and an initial migration matching the current schema.
- [x] Add local helpers (`just db-up`, `just migrate`) and basic docs.
- [x] Update CI to run migrations (Postgres service + `alembic upgrade head`) before tests.
- [x] Migrate incrementally: `courses` first, then `paths` + `path_courses`, then `tracking`, then `auth` + `sessions`.
- [x] Move API integration tests to `httpx.AsyncClient` + `pytest-anyio`.
- [x] Replace global service singletons (`*_service = ...`) with per-request construction from `AsyncSession` in `backend/api/deps.py` (and move routers to `async def`).
- [x] Decide Postgres seeding strategy: do not seed automatically (no app startup seed).
- [x] Add operational defaults (pool sizing/timeouts) and safe migration execution (avoid concurrent migration runs).
- [x] Regenerate and commit `uv.lock` after dependency changes (keep CI/Docker `uv sync --frozen` working).

## Phase 4b — Postgres Hardening
- [x] Add FK constraints for domain integrity (e.g. `tracking.course_id -> courses.id`, `sessions.colleague_id -> users.username`).
- [x] Enforce uniqueness for sessions (`sessions.token_hash UNIQUE`).
- [x] Standardize “not found” behavior to `404` (avoid `200` + `{"error":"not_found"}` patterns).
- [x] Standardize error envelopes for `HTTPException` and request validation errors (Pydantic/FastAPI) to match domain `ServiceError` responses.
- [x] Ensure strict UTC ISO-8601 timestamps with tests (TIMESTAMPTZ migration deferred).
- [x] Revisit transaction boundaries: avoid opening explicit transactions for read-only operations unless needed.

## Phase 5 — UI migration to NiceGUI
- [x] Create NiceGUI shell app with shared navigation and layout.
- [x] Adopt frontend architecture: pages + components + services + `ApiClient` + `SessionStore` (`docs/architecture_frontend.md`).
- [x] Implement `ApiClient` with `X-Session-Token` injection and standard error mapping.
- [x] Implement `SessionStore` for token persistence + current-user loading (`/auth/me`).
- [x] Port login/session flow to NiceGUI (reuse backend auth).
- [x] Port core pages: Home/Dashboard, Courses, My Courses.
- [x] Port Paths + My Paths (including ordering UI and admin edit flows).
- [x] Enforce consistent page layout: wrap all page content (filters/actions/tables) inside `render_container()`.
- [x] Add minimal AI curator: `POST /ai/plan` returns “draft path + draft courses” (no DB writes) + NiceGUI review/apply page.
- [x] Introduce frontend “services/use-cases” layer to keep pages thin and reduce duplicated orchestration (courses+tracking, paths+selected, dashboard aggregates).
- [x] Make navigation role-aware (hide admin-only routes in the shell unless `role == "admin"`).
- [x] Remove cross-page coupling by moving shared UI helpers (e.g. status chip helpers) into shared `components/` utilities.
- [x] Improve `ApiClient` runtime behavior: reuse a persistent `httpx.AsyncClient` for connection pooling.
- [x] Improve `ApiClient` resilience: map `httpx.RequestError` into a user-friendly `ApiError`.
- [x] Parity check + remove Streamlit UI once stable.

## Phase 9 — Product UX Polish (NiceGUI)
- [x] Upgrade loading states: skeletons/spinners for tables/cards (avoid “Loading…” text-only).
- [x] Add clear empty-state CTAs (Courses/Paths/My Courses/My Paths) linking to the next action.
- [x] Home: “Continue learning” section (top `in_progress` courses) with quick actions (open link, mark completed).
- [x] Home: “Next up” section derived from selected paths (first non-completed course per path).
- [x] Courses/My Courses: inline tracking status updates (no modal required) + consistent metadata chips.
- [x] My Paths: show per-path progress at a glance (completed/total + bar) without opening details.
- [x] Navigation polish: active route highlighting and optional feature flags (hide AI Curator unless enabled).
- [x] Debounce search inputs to reduce backend load (avoid requests per keystroke).
- [x] Add an “Articles” section where users can share links (title, URL, tags) and browse/search community submissions.
- [x] Courses UX: add sort control with sensible defaults (Recommended/Top rated/Most reviewed/Newest/A–Z).
- [x] Courses UX: enhance empty states (show active filters + single “Reset all” CTA; “Share the first course” for empty catalog).
- [x] Courses UX: add facet counts for provider/category/status options.
- [x] Courses UX: paginate or add “Load more”/infinite scroll for large catalogs.
- [x] Courses UX: polish card actions (status as clearer control; optional “Copy link” quick action).
- [x] Courses UX: highlight “new/updated” courses and add a “Recently added” sort.


## Phase 10 — Social Layer (By Colleagues, For Colleagues)

### Phase 10A — P0 Foundation (Highest Priority)
- [x] Ownership + permissions: allow any authenticated user to create courses/paths; only the creator (or admin) can edit/delete; admin can edit/delete everything.
- [x] Add reviews for courses (rating + text) with basic moderation/admin removal.
- [x] Add reviews for paths (text) with basic moderation/admin removal.
- [x] Add reviews for articles (rating + text) with basic moderation/admin removal.
- [x] Navigation/IA: merge "My Courses" into `Courses` with `All/Tracked` toggle and redirect `/courses/my` → `/courses?tab=tracked`.
- [x] Navigation/IA: merge "My Paths" into `Paths` with `All/Selected` toggle and redirect `/paths/my` → `/paths?tab=selected`.
- [x] Navigation/IA: add a "My learning" page with tabs `Learning` (tracked/selected/saved) and `Shared` (content you created) across Courses/Paths/Articles.
- [x] Product UX: make `My learning` the default post-login landing page and prioritize “Continue next” + “Needs your review”.
- [x] Product UX/IA: rename `Home` to `Insights` and trim overlap with `My learning` (personal execution vs team insights split).

### Phase 10B — P1 Social Product Loop
- [x] Add peer recommendations for courses/paths (who shared/recommended + optional note + timestamp).
- [x] Product UX: add “Shared with you” / “Recommended for you” on `My learning` with save/dismiss actions and “why this was shared” explanation.
- [x] Product UX: strengthen social trust signals on cards/details (shared by, avg rating + count, recent activity, endorsements).
- [x] Product UX: improve contribution loop (quick-share flow with optional note + feedback on teammate engagement).
- [x] Product UX: improve path outcomes UX (milestones + next actionable step + completion impact).
- [x] Product UX: add basic team visibility dashboard (top contributors).
- [x] Add “Quick share course/path” flow (instant publish for authenticated users) with optional draft mode for feedback-before-publish.
- [x] Basic de-duplication for newly shared courses (URL-based + title/provider similarity).
- [x] Notifications v1 (optional): show “shared/recommended for you” inbox or activity feed (no email).

### Phase 10C — P2 Content + AI Readiness
- [x] Course content description: add `courses.description` (short summary) and surface it across UI; keep `level` optional and de-emphasize (hide behind “more filters”) before deciding to drop it.
- [x] AI-ready metadata: add/standardize course content fields (`description`, optional `learning_outcomes`, `prerequisites`, `language`) and define a derived “search document” that combines course + review text for later AI search/planning.
- [x] Copy/wording shift: complete UI label migration from admin CRUD (“New course/path”) to social contribution (“Share course/path”) now that ownership/permissions is live.

### Phase 10D — P2 Frontend Architecture/Clean Code
- [x] Frontend architecture alignment: move My Learning tracking mutations (`set/clear`) into service/use-case layer so page stays UI-only.
- [x] Frontend architecture alignment: extract remaining Paths orchestration (select/unselect + selected detail/tracking refresh flow) into `paths_service.py` use-cases.
- [x] Frontend architecture alignment: remove temporary page-level service shims (e.g., `_load_paths_page_data` compat wrapper) and call service layer directly.
- [x] Frontend architecture alignment: add `admin_users_service.py` and `ai_curator_service.py` to keep page modules focused on UI composition/event binding.
- [x] Frontend clean code: enforce page boundary (pages = UI composition/event binding; move API orchestration to services/use-cases).
- [x] Frontend clean code: introduce typed page state/view-model objects to reduce large closure state (`nonlocal`) usage.
- [x] Frontend clean code: extract large nested handlers into domain action modules (`learning_actions`, `courses_actions`, `paths_actions`).
- [x] Frontend clean code: componentize repeated page sections (top bar, filter rail, card sections, load-more footer).
- [x] Frontend clean code: reduce page-module size/complexity (`courses.py`, `paths.py`, `learning.py`) by splitting into focused UI sections and action modules.
- [x] Frontend clean code: centralize deep-link and intent navigation logic in a shared navigation helper.
- [x] Frontend clean code: standardize mutation flow (optimistic update + rollback + notification + targeted refresh) across pages.
- [x] Frontend clean code: add lightweight page-state reducers/helpers to tame `nonlocal` sprawl and make state transitions explicit/testable.
- [x] Frontend clean code: increase service/use-case unit tests to cover extracted orchestration logic.
- [x] Performance polish: avoid full list reloads after small actions (optimistic UI updates for tracking/reviews), parallelize detail fetches, and add lightweight caching for `/courses/{id}` and reviews.

### Phase 10E — P2 Architecture Hardening (Coupling + Clean Code)
- [x] Frontend boundary hardening: remove remaining `ApiClient` calls from UI flow modules (`dialogs.py`, `detail_flow.py`) and route through page controllers/services.
- [x] Frontend boundary hardening: enforce "no direct `api.get/post/put/delete` in `page.py`/UI flow modules" with architecture guard tests.
- [x] Backend coupling reduction: extract repeated owner/admin authorization checks from routers into reusable policy dependencies/helpers.
- [x] Backend clean code: standardize review/recommendation endpoint authorization and not-found handling via shared helpers to reduce duplicated branch logic.
- [x] Persistence best practice: migrate high-value timestamp-like text columns to typed timezone-aware datetime (`sessions.*`, `tracking.updated_at`) with safe casts and repository compatibility shims.
- [x] Architecture quality gates: keep docs and architecture guards in lock-step; add CI check that fails on architecture doc/guard drift.
- [x] Complexity follow-up: split `courses/page.py` and `paths/page.py` orchestration blocks into `orchestration.py` helpers (`load`, `filter reset`, `list refresh`) to reduce page-level complexity.
- [x] Reliability follow-up: replaced broad `except Exception` fallbacks in frontend services/controllers with typed `ApiError` handling + structured context logging where fallback behavior is intentional.
- [x] Reuse follow-up: centralized duplicated review/recommendation summary formatting helpers into shared utilities and reused across courses/paths/articles/learning.
- [x] Persistence follow-up: completed phased migration of remaining text timestamp columns to typed timezone-aware datetime (sessions/tracking/users/content/reviews/recommendations/user_paths).
  - [x] Phase slice: migrated `users.created_at/updated_at/last_login_at` and `user_paths.created_at/updated_at` to `TIMESTAMPTZ` with repository compatibility shims.
  - [x] Phase slice: migrated `courses.created_at`, `articles.created_at`, and all `*_reviews.created_at` / `*_recommendations.created_at` to `TIMESTAMPTZ` with repository compatibility shims.
- [x] Docs follow-up: resolved remaining backend architecture doc drift (tracking stats auth sequence, reviews/recommendations coverage, and notifications flow notes) to keep diagrams implementation-accurate.
- [x] Transaction boundary hardening: introduced shared `session_scope(...)` in backend services to avoid nested transaction failures when services are composed.
- [x] Typing hardening: started replacing untyped service payload dict handling with pydantic dataclass payloads (courses/paths mutation flows) plus regression tests.
- [x] Frontend reliability guard: removed broad `except Exception` handlers from page modules and added an architecture test to prevent reintroduction.
- [x] Backend complexity reduction: refactor `NotificationsService.list_activity` into composable event-builder functions + shared normalize/dedupe/sort pipeline with focused unit tests.
- [x] Backend typing hardening: tighten service-boundary dataclass fields (prefer strict types over broad `int | str | None`) and remove post-parse coercion branches where possible.
- [x] Boundary ownership cleanup: reduce duplicate router/service validation paths (especially tracking/path-status flows) and standardize error semantics by layer.
- [x] Architecture guard maintainability: evolve backend payload-boundary guard from a fully hardcoded method map to a mixed explicit+convention strategy to reduce brittle refactor churn.
- [x] Backend docs fidelity: add a short enforceable matrix in `docs/architecture_backend.md` mapping service entrypoints -> `_parse_*` helpers -> architecture tests.
- [x] Transaction boundary decoupling: remove reliance on SQLAlchemy transaction internals in `session_scope`; adopt explicit app-level transaction ownership (request-scoped unit-of-work/dependency) and keep services transaction-agnostic.
- [x] Transaction reliability guard: add focused tests for explicit transaction vs implicit request transaction behavior (commit/rollback semantics) without inspecting ORM internal transaction-origin fields.
- [x] Notifications domain typing: replace stringly-typed activity event dict assembly with a typed `ActivityEvent` model (dataclass/TypedDict + enum-like constants) and central event builder utilities.
- [x] Frontend controller boundary hardening: enforce that `pages/*/controller.py` modules do not import NiceGUI UI primitives (`nicegui.ui`) and remain UI-framework agnostic.
- [x] Frontend controller/view split: move remaining action orchestration closures from `courses/page.py` and `paths/page.py` into controller/use-case functions to reduce page modules to composition/binding.
  - [x] Phase slice: extracted `paths` select/unselect side-effect orchestration from `paths/page.py` into `paths/orchestration.py` with focused unit coverage.
  - [x] Phase slice: extracted `paths` create/update/delete + recommendation-summary refresh flows from `paths/page.py` into `paths/orchestration.py` and removed nested page closures.
  - [x] Phase slice: removed `paths/page.py` thin forwarding wrappers (`_create_submit`, `_open_edit`) by wiring share/edit flows directly to orchestration/dialog callbacks.
  - [x] Phase slice: extracted `courses` tracking/recommendation-refresh side-effect orchestration from `courses/page.py` into `courses/orchestration.py` with focused unit coverage.
  - [x] Phase slice: extracted `courses` create/update/delete mutation-reload flows from `courses/page.py` into `courses/orchestration.py` with focused unit coverage.
  - [x] Phase slice: removed remaining nested recommendation-refresh closure in `courses/page.py` by wiring `on_saved` directly to orchestration helper (`functools.partial`).
  - [x] Phase slice: extracted `courses` details-dialog callback wiring from `courses/page.py` into `courses/detail_flow.py` (`open_course_details_flow`) with focused unit coverage.
  - [x] Phase slice: removed `courses/page.py` delete-confirm wrappers by routing dialog-driven delete flow through orchestration adapters (`open_delete_course_confirmation`, `perform_delete_course_from_dialog`).
  - [x] Phase slice: removed `courses/page.py` thin share/edit forwarding wrappers by wiring create/update flows directly to orchestration callbacks.
  - [x] Phase slice: extracted `articles` list-load lifecycle (`loading/meta/success/failure/facet-refresh`) from `articles/page.py` into `articles/orchestration.py` with focused unit coverage.
  - [x] Phase slice: extracted `articles` share-create + reload flow from `articles/page.py` into `articles/orchestration.py` with focused unit coverage.
  - [x] Phase slice: extracted `articles` filter refresh/reset list orchestration from `articles/page.py` into `articles/orchestration.py` with focused unit coverage.
  - [x] Phase slice: extracted `articles` facet-controls recompute + active-filter clear-by-key logic from `articles/page.py` into `articles/actions.py` with focused unit coverage.
  - [x] Phase slice: extracted `articles` details-dialog callback orchestration from `articles/page.py` into `articles/detail_flow.py` with focused unit coverage.
  - [x] Phase slice: removed remaining nested reset-filter closures from `articles/page.py` via typed control reset helper (`articles/actions.py`) wired through orchestration.
  - [x] Phase slice: removed `_recompute_facets` closure from `articles/page.py` via explicit-search facet helper in `articles/actions.py` and rewired load/reset/refresh call sites.
  - [x] Phase slice: removed nested active-filter clear closure from `articles/page.py` by introducing reusable `clear+refresh` action helper with focused unit coverage.
  - [x] Phase slice: introduced `build_articles_facet_controls(...)` helper to deduplicate repeated control-bundle construction in `articles/page.py` and removed stale imports.
  - [x] Phase slice: centralized `articles/page.py` facet-control bundle creation behind one local helper to reduce repeated inline wiring across load/reset/refresh callbacks.
- [x] Frontend view-model boundary: require `page.py` card rendering paths to consume typed view-model mappers (no inline shape coercion in page modules).
  - [x] Phase slice: added architecture guard asserting key page modules (`courses`, `paths`, `articles`, `learning`) import and call their page-local view-model mapper/builders.
  - [x] Phase slice: introduced `articles/view_model.py` and migrated article-card display coercion from `articles/page.py` into typed mapper.
- [x] Frontend complexity guard: add architecture checks that flag oversized page modules and force extraction into `controller.py`/`orchestration.py`/`sections.py`.
  - [x] Phase slice: added frontend architecture test capping major page module size (guardrail: <= 550 LOC for `courses`, `paths`, `articles`, `learning` page modules).

## Phase 11 — Operability + Quality

### Phase 11A — UX & Visual System

#### Phase 11A.1 — Design System Foundations
- [x] Styling system refresh: define shared design tokens (spacing, typography scale, radii, shadows, semantic colors) and apply globally.
- [x] Styling system refresh: refine color system (keep blue identity, increase surface contrast steps, strengthen semantic accents for primary/success/warning/error).
- [x] Styling system refresh: run a layout rhythm/density pass across topbars, filter rails, cards, dialogs, and section spacing.
- [x] Styling/layout refresh: improve perceived page width (collapsible filter rail, wider content container, responsive drawer-mode filters on narrower desktop/tablet).
- [x] Styling system refresh: standardize interaction states (hover/focus/active/disabled), improve contrast/focus visibility, and add subtle motion polish.
- [x] UX typography: apply a consistent type scale and weights across topbars, cards, rails, and dialogs.
- [x] UX productivity: keep key list controls visible on scroll (sticky topbar/list controls where appropriate).
- [x] Theming architecture hardening: introduce a variant-driven theme API and add tests/guards to prevent layout drift or ad-hoc per-page CSS forks.
- [ ] Modernization Sprint 1 (structure): finalize typography scale + spacing rhythm + single component language (cards/buttons/chips/inputs) across all core pages.

#### Phase 11A.2 — Catalog Layout & Card UX
- [x] Catalog IA/layout system: keep one shared list-page skeleton (topbar + filter pattern + featured/rails/list composition) across Courses/Articles/Paths to preserve familiarity.
- [x] Catalog visual variants: define per-page style variants (Courses/Articles/Paths) with shared base tokens and page-specific accent tokens (surface blend, chips, highlights).
- [x] UX polish: strengthen card hierarchy (title/meta/chip priority), reduce action-row noise, and standardize primary vs secondary actions.
- [x] UX polish: make filter UX progressive (top 2-3 always visible, remaining filters behind “More filters”).
- [x] UX polish: unify empty/loading/error states across core pages with consistent CTA patterns.
- [x] Card consistency pass: enforce one shared course card skeleton (title/meta/chips/actions/media slots) so all cards keep identical spacing and scan rhythm.
  - [x] Phase slice: normalized Courses cards to a stable content+media layout with a consistent right media slot and placeholder for non-media courses.
- [x] Action hierarchy pass: simplify card action row to one clear primary CTA + one secondary action + status control; move lower-priority actions into overflow.
  - [x] Phase slice: simplified Courses card actions by moving `Details` into overflow and keeping action row focused on primary CTA + status (+ optional preview for media cards).
- [x] Topbar clarity pass: rebalance control weight by prioritizing search and visually grouping view/sort/share/count as secondary controls.
  - [x] Phase slice: de-emphasized secondary topbar controls (view/sort/share/count) and tuned visual weight so search remains primary on Courses.
- [x] Filter rail density pass: reduce rail visual weight (contrast/width) so content remains primary while preserving filter discoverability.
  - [x] Phase slice: reduced rail width and lowered rail contrast/shadow intensity to shift visual focus back to the content column.
- [x] Filter rail visual-weight pass (catalog pages): further de-emphasize rail contrast/surface treatment so primary content cards remain the dominant focal point.
- [x] Content-type hierarchy pass (in progress): tune card information priority per domain (Courses: progression/status; Articles: author/date/editorial metadata; Paths: milestones/progress sequencing).
  - [x] Phase slice: accepted Explore course-card UX baseline (compact premium card rhythm, primary CTA clarity, and reduced metadata density).
  - [x] Phase slice: align Explore path and article cards to the same visual rhythm/slot model as the accepted course cards (title/meta/status/action baselines + spacing parity).
- [x] Articles UX follow-up (empty-state composition): avoid hero + empty-card message duplication; introduce a compact empty variant so first-load pages do not feel content-sparse.
- [x] Topbar clarity follow-up (Articles): add explicit sort labeling/grouping and separate count metadata from action controls for faster scan.
- [x] Empty-state density polish (Articles): tighten headline/body spacing and reduce vertical whitespace in the empty block while preserving CTA prominence.

#### Phase 11A.3 — Media & Thumbnail Pipeline
- [x] Course media UX: support embedded course videos when source is YouTube (validated URL parsing, safe embed iframe, and fallback external link).
- [x] Articles media UX: show source thumbnails on article cards (Articles + Explore) using resolved preview metadata.
- [x] URL metadata suggestions API: add authenticated `POST /url-preview/metadata` endpoint returning normalized URL + title/description/site name/preview image + suggested provider/category/tags.
- [x] URL metadata service expansion: extend `UrlPreviewService` with metadata parsing (Open Graph + meta description/keywords + title fallback) and lightweight domain/tag/category heuristics.
- [x] URL metadata service reuse: inject one shared `UrlPreviewService` instance via API dependencies so preview + metadata caching works across requests.
- [x] Share dialog autofill (Courses): add “Suggest from URL” action to prefill empty fields (`title`, `description`, `provider`, `category`) and optional topic hints from suggested tags.
- [x] Share dialog autofill (Articles): add “Suggest from URL” action to prefill empty fields (`title`, `tags`) and normalize source URL before submit.
- [x] Share flow UX (Courses/Articles): trigger metadata suggestions automatically on URL paste/blur with debounce, while keeping the manual “Suggest from URL” control.
- [x] Share flow UX (Courses/Articles): show inline “suggested vs edited” indicators so users can quickly trust/override autofilled values.
- [x] Share flow validation (Courses/Articles): add live URL validation and duplicate checks before submit (existing URL/domain/title-provider hints) with actionable inline messages.
- [x] Share flow reliability (Courses/Articles): persist unsent draft form state with autosave + recovery after refresh/navigation and explicit “discard draft” action.
- [x] Share flow productivity (Courses/Articles): add one-click “apply all suggestions” and per-field “re-suggest” actions for faster curation.
- [x] Share flow safety (Courses/Articles): provide “metadata unavailable” fallback UX with smart placeholders/examples so users can still submit quickly.
- [x] Share flow post-submit: show contextual success summary (what was autofilled/saved) and quick follow-up actions (open item, copy link, add review/recommendation).
- [ ] Course media enrichment: extend thumbnail resolution beyond YouTube using provider APIs/oEmbed first, then metadata scraping fallback (`og:image`/`twitter:image`) with caching and SSRF-safe fetch constraints.
- [ ] Course + Article URL metadata persistence: persist fetched source metadata on create/update (`preview_image_url`, source title/site/description/canonical URL, `metadata_fetched_at`) with optional manual refresh action; avoid per-list live re-scraping.
- [ ] Thumbnail quality gate: reject blurry/low-quality preview images via server-side image sharpness checks (e.g., Laplacian variance threshold) and fallback to alternate metadata candidates.
- [ ] Thumbnail fallback policy: when quality gate or fetch checks reject a source image, use a first-party default branded fallback thumbnail.
- [ ] Media placement polish: standardize thumbnail alignment/offset rules relative to top-right card controls (`New`/menu) and card content baseline.
  - [x] Phase slice: replaced ad-hoc thumbnail margins with media-slot alignment rules (fixed top/right slot padding), and changed non-media placeholder to compact pill style to remove dead-card space.

#### Phase 11A.4 — Page Identity & Motion Polish
- [ ] Motion polish: add subtle transitions for refreshes, filter expand/collapse, and card state updates.
- [x] motion + micro-interaction foundation (card enter/stagger feel, richer button/chip hover-press states, and subtle control transitions).
- [ ] Page identity pass (in progress): add page-specific section language and hero treatments (without changing interaction model) so catalog pages feel distinct but consistent.
- [ ] Modernization Sprint 2 (interaction): add cohesive motion system (120-200ms transitions, list stagger, filter/sort state transitions) and stronger inline feedback patterns.
- [ ] Modernization Sprint 3 (product feel): refine surface/depth system (contrast steps/shadows), emphasize social signals (owner/recommendation/review context), and complete accessibility/focus polish.

### Phase 11B — Activity Feed UX v2
- [ ] Activity feed UX v2: add filters (`All`, `Recommendations`, `Ratings`, `Courses`, `Paths`, `Articles`).
- [ ] Activity feed UX v2: add unread state + mailbox badge + “Mark all read”.
- [ ] Activity feed UX v2: add relative timestamps with absolute time on hover.
- [ ] Activity feed UX v2: add pagination/“Load more” for older events.
- [ ] Activity feed UX v2: improve article deep-linking to open the specific item context.
- [ ] Activity feed UX v2: group burst events and rank high-signal events higher (e.g., ratings on your shared content).
- [ ] Activity feed correctness: sort by parsed timezone-aware datetimes (not raw timestamp strings) to guarantee true chronological ordering across offsets.
- [ ] Activity feed resilience: skip malformed activity rows (bad ids/ratings/timestamps), log structured context, and continue returning valid events.

### Phase 11C — Reliability & Accessibility
- [ ] Notification resilience hardening: enrich `safe_notify` logs with action/page context, add optional strict mode for dev/test, and add regression tests for deleted-slot notification paths.
- [ ] Observability: add frontend telemetry for core actions (share/select/review/complete) and page-level error tracking.
- [ ] Accessibility UX: improve keyboard navigation and focus management for menus, dropdowns, dialogs, and card actions.
- [ ] Accessibility pass: keyboard navigation, visible focus states, ARIA labels for icon-only actions, and contrast audit fixes.
- [ ] Resilience UX: network/offline banner, retry affordances, and standardized section-level error states.
- [ ] Performance: short-TTL client caching for hot reads (`/tracking`, review summaries), batched detail fetches, and fewer full reloads after mutations.

### Phase 11D — Quality Gates & Test Stability
- [ ] Quality gates: add visual regression checks for key pages and smoke e2e flows (login, track course, review, select path).
  - [x] Phase slice: add Playwright smoke coverage for `login` + `track` with CI artifact uploads (screenshots + app logs).
  - [x] Phase slice: extend smoke coverage to `review` + `select path`.
  - [x] Phase slice: add visual-regression snapshot assertion harness + baseline update workflow.
  - [ ] Phase slice: commit stable baseline images and enable strict visual-regression enforcement in CI.
- [x] Test reliability: isolate backend integration test auth/session state per test (or per module) to remove intermittent `401/404/500` flakiness.
- [x] Docs sync: update `docs/architecture_frontend.md` to match current IA/routes (`My learning`, `Insights`, mailbox activity) and current service/page boundaries.
- [x] Docs sync: update `docs/architecture_backend.md` course/recommendation/review model details (`description`, `learning_outcomes`, `prerequisites`, `language`, `search_document`) and current service flows.
- [x] Lint/mypy ratchet (near-term target): converge to `mccabe<=25`, `max-branches<=20`, `max-statements<=100`, `max-args<=10`, `max-returns<=8` for non-legacy code.
  - [x] Phase slice: define enforcement tiers by module type (strict for `services/controllers/orchestration/reducers`; slightly looser for UI section renderers) and document them in `pyproject.toml` comments.
  - [x] Phase slice: remove temporary per-file complexity ignores from active (non-legacy) modules by extracting oversized functions into `controller.py`, `orchestration.py`, `actions.py`, and `ui_glue.py`.
  - [x] Phase slice: reduce argument-heavy APIs (`PLR0913`) by introducing typed payload/view-model dataclasses and callback/context objects instead of long parameter lists.
  - [x] Phase slice: add architecture tests that prevent new direct complexity regressions in active page modules (file-size + complexity smoke guards).
  - [x] Phase slice: keep legacy pages explicitly excluded until migration is complete; do not expand legacy ignore scope.
  - [x] Phase slice: enable CI ratchet mode (fail on new violations first, then fail on full threshold) to tighten incrementally without blocking delivery.
  - [x] Phase slice: enforce target thresholds in `pyproject.toml` and refactor remaining non-legacy violations to keep full `ruff` + scoped `mypy` green.

### Phase 11E — IA Simplification + First-Use Clarity

Goal: reduce cognitive load and make the core loop understandable in the first 2-3 minutes.

Success criteria:
- [ ] First-use comprehension: a new user can describe the product in one sentence within 5 minutes.
- [ ] Time-to-first-meaningful-action: `< 60s` from login to first `track` or `share`.
- [x] Top-level navigation: max 4 items (`Home`, `Explore`, `Teams`, `Profile`).
- [ ] IA consistency: no conceptual duplication across primary pages.

Execution sequencing (prioritized):
- [x] Phase 11E.0 (instrumentation baseline): add telemetry for first meaningful action (`track`/`share`), first search, primary-nav clicks, and page exits so pre/post redesign impact is measurable.
- [x] Phase 11E.1 (IA + terminology foundation): ship nav reduction + naming alignment first to establish a stable mental model before page-level redesign.
- [x] Phase 11E.2 (home/explore behavior): redesign `Home` and `Explore` around one dominant action each.
- [ ] Phase 11E.3 (first-time clarity): complete intro + empty-state clarity pass and keep next-step clarity explicit across primary pages.

#### Phase 11E.1 — Top-Level Navigation Simplification
- [x] Navigation reduction: keep only `Home`, `Explore`, `Teams`, `Profile` in top-level shell nav.
- [x] Navigation cleanup: remove `Insights` from top-level navigation.
- [x] Navigation cleanup: remove standalone `Courses`, `Paths`, and `Articles` from top-level navigation.
- [x] Navigation consistency: enforce active-route highlighting and simplified menu structure across all routes.
- [x] Navigation audit: remove low-frequency routes from primary nav and keep them in contextual menus/overflow.

#### Phase 11E.2 — Merge & Reorganize Primary Pages
- [x] IA merge: combine `My Learning` + `Insights` into new `Home`.
- [x] IA relocation: move full statistics dashboard to `Profile > Stats`.
- [x] IA consolidation: merge `Courses`, `Paths`, and `Articles` into `Explore` with tabs (`All`, `Courses`, `Paths`, `Articles`).
- [x] IA dedupe: remove redundant discovery sections duplicated between `Explore` and catalog-specific pages.

#### Phase 11E.3 — Home Redesign (Action-Oriented Hub)
- [x] Home hero priority: make `Continue learning` the dominant above-the-fold section.
- [x] Home density reduction: collapse review nudges into a compact secondary block.
- [x] Home social loop: add `Recently shared in your teams`.
- [x] Home stats containment: show at most 3 snapshot cards with link to full stats in `Profile > Stats`.
- [x] Home CTA hierarchy: ensure only one dominant CTA above the fold.

#### Phase 11E.4 — Explore as Single Discovery Hub
- [x] Explore hierarchy: make search the dominant visual control.
- [x] Explore filtering: implement tab-based type filtering (`All`, `Courses`, `Paths`, `Articles`).
- [x] Explore dedupe: remove duplicated `featured` logic inherited from `Courses`.
- [x] Explore consistency: standardize card structure across content types.
  - [x] Phase slice: course cards finalized as the Explore reference pattern.
  - [x] Phase slice: finish path/article card parity with course-card structure and CTA baseline alignment.
- [x] Explore card actions: ensure one primary action per card.
- [x] Explore details navigation: replace hover/dialog-first detail behavior with dedicated detail routes per content type (course/path/article) and keep cards focused on scan + primary action.
- [x] Legacy catalog cleanup: convert `/courses`, `/paths`, and `/articles` to thin compatibility routes (deep-link/management only), remove duplicated discovery UI, and complete redirect/deprecation plan after Explore detail parity is stable.

#### Phase 11E.5 — Visual & Action Density Reduction
- [x] Card action limit: cap card controls to 1 primary CTA + 1 state control (`track`/`select`) + overflow for secondary actions.
- [x] Filter-rail weight: reduce filter rail visual dominance so content remains primary.
- [x] Metadata pruning: remove redundant metadata from default card view.
- [x] Topbar hierarchy: de-emphasize secondary controls (`sort`, `view`, `share`) relative to search and core action.

#### Phase 11E.6 — Terminology Alignment
- [x] Rename `My Learning` -> `Home` in copy, routes, and references.
- [x] Terminology audit: align `Track` vs `Save` vs `Select` and choose one canonical term per intent.
- [x] Terminology audit: align `Shared` vs `Recommended` semantics in UI labels and filters.
- [x] Terminology audit: align `Insights` vs `Stats` and reserve `Stats` for analytics surfaces.
- [x] Context subtitles: add a short purpose subtitle under each primary page title.
- [x] Cross-page consistency: use the same language model across course/path/article cards and detail dialogs.

#### Phase 11E.7 — First-Time User Clarity Pass
- [x] Onboarding intro: add lightweight, dismissible 3-step first-login walkthrough.
- [x] Empty states: ensure each empty state has exactly one clear primary action.
- [x] Next-step clarity: no page should load without an unambiguous next step.

Definition of done:
- [ ] Navigation feels obvious without explanation.
- [ ] `Home` clearly answers "What should I do next?"
- [ ] `Explore` clearly answers "What can I discover?"

Implementation map (routes + files, ordered):
- [x] Route transition contract finalized: canonical routes are `/home`, `/explore`, `/teams`, `/profile`, `/profile/stats`, and Explore detail routes (`/explore/courses/{id}`, `/explore/paths/{id}`, `/explore/articles/{id}`); legacy aliases and compatibility discovery routes removed.
- [x] Phase 11E.0 instrumentation baseline:
  - Primary files: `frontend/ui/nicegui/core/api_client.py`, `frontend/ui/nicegui/core/navigation.py`, `frontend/ui/nicegui/pages/login/page.py`, `frontend/ui/nicegui/pages/home/page.py`, `frontend/ui/nicegui/pages/explore/page.py`.
  - New modules (if needed): `frontend/ui/nicegui/services/telemetry_service.py`, backend endpoint under `backend/api/` + service in `backend/services/`.
  - Event checkpoints: login success, first nav click, first search, first `track`, first `share`, first meaningful action timestamp.
- [x] Phase 11E.1 navigation simplification:
  - Primary files: `frontend/ui/nicegui/components/layout.py` (top-level menu), `frontend/ui/nicegui/main.py` (route registration), `frontend/ui/nicegui/pages/home/page.py` (home route binding), `frontend/ui/nicegui/core/guards.py` (non-admin fallback route), `frontend/ui/nicegui/core/navigation.py` (tab/deep-link helpers).
  - New page packages to add: `frontend/ui/nicegui/pages/teams/`, `frontend/ui/nicegui/pages/profile/`.
  - Test/docs updates: `tests/frontend/ui/nicegui/test_routes.py`, `tests/frontend/ui/nicegui/core/test_core_navigation.py`, `tests/frontend/ui/nicegui/test_architecture_docs_contracts.py`, `docs/architecture_frontend.md`.
- [x] Phase 11E.2 page merge + IA reorganization:
  - Home merge (`My learning` + `Insights`): `frontend/ui/nicegui/pages/home/page.py`, `frontend/ui/nicegui/pages/home/sections.py`, `frontend/ui/nicegui/pages/home/controller.py`, `frontend/ui/nicegui/pages/home/state.py`, `frontend/ui/nicegui/services/learning_service.py`, `frontend/ui/nicegui/services/dashboard_service.py`.
  - Explore consolidation (Courses/Paths/Articles): `frontend/ui/nicegui/pages/explore/page.py`, `frontend/ui/nicegui/pages/explore/sections.py`, `frontend/ui/nicegui/pages/explore/orchestration.py`, `frontend/ui/nicegui/pages/explore/state.py`, `frontend/ui/nicegui/pages/explore/ui_glue.py`, plus card adapters from `pages/courses/view_model.py`, `pages/paths/view_model.py`, `pages/articles/view_model.py`.
  - Stats relocation: create `frontend/ui/nicegui/pages/profile/page.py` and move full stats rendering from current insights/home blocks into `Profile > Stats`.
- [x] Phase 11E.3 home redesign (action-oriented):
  - Primary files: `frontend/ui/nicegui/pages/home/sections.py` (hero + compact review nudges + team shares), `frontend/ui/nicegui/pages/home/page.py` (layout hierarchy + single dominant CTA), `frontend/ui/nicegui/pages/home/controller.py` (load ordering), `frontend/ui/nicegui/core/theme.py` (above-the-fold emphasis styles).
  - Data feeds likely reused: learning progression from `frontend/ui/nicegui/services/learning_service.py`, team-share activity from `frontend/ui/nicegui/services/notifications_service.py`.
- [x] Phase 11E.4 explore hub redesign:
  - Primary files: `frontend/ui/nicegui/pages/explore/sections.py` (search-dominant topbar + tabs), `frontend/ui/nicegui/pages/explore/page.py` (single discovery flow), `frontend/ui/nicegui/pages/explore/orchestration.py` (unified load/filter pipeline), `frontend/ui/nicegui/core/theme.py` (card consistency tokens).
  - Remove duplicate discovery logic from standalone catalogs after parity: `frontend/ui/nicegui/pages/courses/page.py`, `frontend/ui/nicegui/pages/paths/page.py`, `frontend/ui/nicegui/pages/articles/page.py`.
- [x] Phase 11E.5 visual/action density reduction:
  - Primary files: `frontend/ui/nicegui/pages/courses/sections.py`, `frontend/ui/nicegui/pages/articles/sections.py`, `frontend/ui/nicegui/components/path_card.py`, `frontend/ui/nicegui/components/card_actions.py`, `frontend/ui/nicegui/pages/explore/sections.py`, `frontend/ui/nicegui/core/theme.py`.
  - Acceptance checks in code: one primary CTA + one state control per card, overflow for secondary actions, reduced metadata defaults.
- [ ] Phase 11E.6 terminology alignment:
  - Primary files: `frontend/ui/nicegui/components/layout.py`, `frontend/ui/nicegui/pages/home/page.py`, `frontend/ui/nicegui/pages/explore/page.py`, `frontend/ui/nicegui/pages/courses/`, `frontend/ui/nicegui/pages/paths/`, `frontend/ui/nicegui/pages/articles/`, `frontend/ui/nicegui/pages/activity/`.
  - Copy + route helper updates: `frontend/ui/nicegui/core/navigation.py`, `frontend/ui/nicegui/pages/learning/route_init.py` (or replacement home route init).
  - Test updates for label/route expectations: `tests/frontend/ui/nicegui/pages/login/test_login_page_integration.py`, `tests/frontend/ui/nicegui/pages/home/test_home_page_integration.py`, `tests/frontend/ui/nicegui/test_architecture_docs_contracts.py`.
- [ ] Phase 11E.7 first-time-user clarity pass:
  - Primary files: add onboarding component (recommended `frontend/ui/nicegui/components/onboarding_intro.py`) and wire in `frontend/ui/nicegui/pages/home/page.py`.
  - Empty-state harmonization targets: `frontend/ui/nicegui/pages/home/sections.py`, `frontend/ui/nicegui/pages/explore/sections.py`, `frontend/ui/nicegui/pages/courses/sections.py`, `frontend/ui/nicegui/pages/paths/sections.py`, `frontend/ui/nicegui/pages/articles/sections.py`.
  - Validation/testing harness: add/update integration tests under `tests/frontend/ui/nicegui/pages/home/` and `tests/frontend/ui/nicegui/pages/explore/` for one-clear-next-action empty states and intro dismiss behavior.
- [ ] Sprint-level execution plan: track active sprint tasks in `docs/sprint.md`.

### Phase 11F — Social Learning Hub v1 (Teams + Scoped Sharing)

Goal: ship a clear collaboration model where discovery stays broad, but social context is team-relevant and privacy-explicit.

Product model (v1):
- [ ] Discovery model: keep `Explore` global for all authenticated users.
- [ ] Sharing audience model: each share supports audience scope (`public`, `my_teams`, `selected_teams`).
- [ ] Visibility contract: every shared item shows an audience badge (who can see this).
- [ ] Home contract: prioritize “what needs my attention” and team-social actions above passive content.
- [ ] Teams contract: team page is the collaboration workspace (members + activity + share context), not only an activity feed.

User flow design (v1):
- [ ] New user with no team:
  - [ ] `Home`: keep learning workflow usable; show lightweight social placeholders with CTA to `/teams`.
  - [ ] `/teams`: show empty state with one primary action (`Create team`) and optional secondary action (`Join team`) when invite flow exists.
- [ ] Team creator activation:
  - [ ] After create, auto-open created team detail.
  - [ ] Show inline “add first member” and “share first item” prompts.
- [ ] Team member with no activity:
  - [ ] Show members and team context.
  - [ ] Show clear empty team-activity state with next action CTA (`Explore to share`).

Backend/API execution (v1+):
- [x] Team domain baseline:
  - [x] `teams`, `team_members` schema + migration.
  - [x] Core endpoints: `POST /teams`, `GET /teams/mine`, `GET /teams/{id}`, member add/remove, team activity.
- [ ] Share audience scoping:
  - [ ] Add team targeting to share persistence (`team_id` or share-target join table).
  - [ ] Add share visibility filtering by audience scope.
  - [ ] Keep backwards compatibility for legacy global shares.
- [ ] Team activity correctness:
  - [ ] Drive activity primarily from team-scoped share/review/recommendation events.
  - [ ] Ensure non-members cannot infer private team activity/content.

Frontend/UI execution (v1+):
- [x] Teams page foundation:
  - [x] My Teams list, create team dialog, team detail, member add/remove, team activity view.
- [ ] Explore share dialog:
  - [ ] Add audience selector (`Public`, `My teams`, `Selected teams`).
  - [ ] Add team multi-select when `Selected teams` is chosen.
  - [ ] Show privacy explanation copy before submit.
- [ ] Home social alignment:
  - [ ] If user has no teams, collapse social panels into low-noise activation placeholders.
  - [ ] If user has teams, show scoped team-social actions (reviews/recommendations/shares needing attention).
- [ ] Shared-tab alignment:
  - [ ] Use the same audience badges and scope semantics as Teams/Home.
  - [ ] Keep visual language consistent with Explore/Home dark professional theme.

Review-request collaboration loop (v1.1):
- [ ] Team review requests:
  - [ ] Add `Request review` action for team-scoped shared items.
  - [ ] Allow selecting one or more reviewers from the same team.
  - [ ] Support optional request note/context.
- [ ] Review-request domain model:
  - [ ] Add `review_requests` persistence (`team_id`, `share_type`, `share_id`, `requested_by`, `requested_for`, `status`, timestamps, note).
  - [ ] Enforce one active open request per `(share, reviewer)` to avoid duplicate noise.
  - [ ] Status lifecycle: `open -> completed | dismissed | canceled`.
- [ ] Review-request API:
  - [ ] `POST /teams/{id}/review-requests`
  - [ ] `GET /teams/{id}/review-requests?status=open`
  - [ ] `GET /review-requests/mine?status=open`
  - [ ] `POST /review-requests/{id}/complete`
  - [ ] `POST /review-requests/{id}/dismiss`
  - [ ] `DELETE /review-requests/{id}` (cancel by requester/admin)
- [ ] Review-request UX:
  - [ ] Home “Conversations needing you” source uses open review requests.
  - [ ] Teams detail exposes open team review requests.
  - [ ] Completing a review offers direct request-completion path.

Conversational course discussions (v1.2):
- [ ] Discussion model (separate from reviews):
  - [ ] Keep reviews as summary feedback (rating + review text), not threaded discussion.
  - [ ] Add thread/message entities for conversational collaboration on courses.
  - [ ] Support team-scoped threads to keep context relevant and private where required.
- [ ] Discussion domain model:
  - [ ] Add `course_discussion_threads` (`id`, `course_id`, `team_id?`, `created_by`, `title`, `status`, timestamps).
  - [ ] Add `course_discussion_messages` (`id`, `thread_id`, `created_by`, `message`, timestamps).
  - [ ] Thread lifecycle: `open -> resolved -> reopened`.
- [ ] Discussion API:
  - [ ] `POST /courses/{id}/discussions` (create thread)
  - [ ] `GET /courses/{id}/discussions`
  - [ ] `GET /discussions/{id}`
  - [ ] `POST /discussions/{id}/messages`
  - [ ] `POST /discussions/{id}/resolve`
  - [ ] `POST /discussions/{id}/reopen`
- [ ] Discussion UX:
  - [ ] Add “Discuss” action on course cards/details where collaboration is available.
  - [ ] Render compact thread timeline in course detail.
  - [ ] Integrate open mentions/replies into “Conversations needing you.”

Success criteria:
- [ ] A first-time user can create or join a team in under 60 seconds.
- [ ] A user can understand “who can see this share” without opening docs/help.
- [ ] Team activity relevance improves (events are attributable to explicit team scope).
- [ ] No regression in core solo-learning loop for users not in teams.
- [ ] Team review requests improve collaboration responsiveness (measured by open->completed conversion and median completion time).
- [ ] Users can have multi-step, thread-based collaboration on courses without overloading review records.

## Phase 12 — Analytics + Data Durability
- [ ] Colleague profiles with interest/completion tracking.
- [ ] Profile avatars:
  - [ ] Allow users to upload/select a profile avatar.
  - [ ] Add backend avatar metadata/storage support (URL/path, size/type validation, replace/remove).
  - [ ] Add profile UI for avatar create/update/remove with preview + fallback initials.
  - [ ] Show avatars consistently across `Home`, `Teams`, `Profile`, and activity/conversation feeds.
- [ ] Basic analytics (popular courses, completion rates).
- [ ] Import/export tools for course data.
- [ ] UI polish + accessibility improvements.
- [ ] Analytics (users): per-user completion metrics (completed/in-progress/interested), review counts, recommendation counts, and contribution trends.
- [ ] Analytics (courses): most-rated courses, highest-rated courses, most-recommended courses, and completion funnel by course.
- [ ] Analytics UI: add sortable leaderboard/table views + chart views for users/courses with date-range filters.

## Phase 13 — Advanced AI Curation (optional)
- [ ] Add an “AI Curator” backend service that turns a user goal into a proposed learning plan (draft path + ordered draft courses).
- [ ] Implement “suggest then approve”: UI preview with edit/remove/reorder before persisting.
- [ ] Add course discovery step (start with constrained sources) and normalize results to the course schema.
- [ ] Add de-duplication heuristics (URL-based + provider/title similarity).
- [ ] Add provenance fields for AI-suggested content (e.g. `source`, `source_url`, `confidence`) and surface them in UI.
- [ ] Run discovery as a background job (avoid blocking request/response; show progress + retries).
- [ ] Persist approved drafts via existing domain services (`CoursesService`, `PathsService`, `TrackingService`) to keep consistency.

## Phase 14 — User Testing + Pilot Validation
- [ ] Run 5 first-time-user usability tests and log confusion points.
- [ ] Fix top 5 confusion points before pilot launch.
- [ ] Add pilot observer confusion-log template + triage rubric.
- [ ] Validate first-session navigation clarity (`"Where do I go?"` confusion rate) after Phase 11 closure.
