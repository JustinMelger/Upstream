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
- [ ] Card consistency pass: enforce one shared course card skeleton (title/meta/chips/actions/media slots) so all cards keep identical spacing and scan rhythm.
  - [x] Phase slice: normalized Courses cards to a stable content+media layout with a consistent right media slot and placeholder for non-media courses.
- [ ] Action hierarchy pass: simplify card action row to one clear primary CTA + one secondary action + status control; move lower-priority actions into overflow.
  - [x] Phase slice: simplified Courses card actions by moving `Details` into overflow and keeping action row focused on primary CTA + status (+ optional preview for media cards).
- [ ] Topbar clarity pass: rebalance control weight by prioritizing search and visually grouping view/sort/share/count as secondary controls.
  - [x] Phase slice: de-emphasized secondary topbar controls (view/sort/share/count) and tuned visual weight so search remains primary on Courses.
- [ ] Filter rail density pass: reduce rail visual weight (contrast/width) so content remains primary while preserving filter discoverability.
  - [x] Phase slice: reduced rail width and lowered rail contrast/shadow intensity to shift visual focus back to the content column.
- [ ] Filter rail visual-weight pass (catalog pages): further de-emphasize rail contrast/surface treatment so primary content cards remain the dominant focal point.
- [ ] Content-type hierarchy pass (in progress): tune card information priority per domain (Courses: progression/status; Articles: author/date/editorial metadata; Paths: milestones/progress sequencing).
- [ ] Articles UX follow-up (empty-state composition): avoid hero + empty-card message duplication; introduce a compact empty variant so first-load pages do not feel content-sparse.
- [ ] Topbar clarity follow-up (Articles): add explicit sort labeling/grouping and separate count metadata from action controls for faster scan.
- [ ] Empty-state density polish (Articles): tighten headline/body spacing and reduce vertical whitespace in the empty block while preserving CTA prominence.

#### Phase 11A.3 — Media & Thumbnail Pipeline
- [x] Course media UX: support embedded course videos when source is YouTube (validated URL parsing, safe embed iframe, and fallback external link).
- [x] Articles media UX: show source thumbnails on article cards (Articles + Explore) using resolved preview metadata.
- [x] URL metadata suggestions API: add authenticated `POST /url-preview/metadata` endpoint returning normalized URL + title/description/site name/preview image + suggested provider/category/tags.
- [x] URL metadata service expansion: extend `UrlPreviewService` with metadata parsing (Open Graph + meta description/keywords + title fallback) and lightweight domain/tag/category heuristics.
- [x] URL metadata service reuse: inject one shared `UrlPreviewService` instance via API dependencies so preview + metadata caching works across requests.
- [x] Share dialog autofill (Courses): add “Suggest from URL” action to prefill empty fields (`title`, `description`, `provider`, `category`) and optional topic hints from suggested tags.
- [x] Share dialog autofill (Articles): add “Suggest from URL” action to prefill empty fields (`title`, `tags`) and normalize source URL before submit.
- [ ] Share flow UX (Courses/Articles): trigger metadata suggestions automatically on URL paste/blur with debounce, while keeping the manual “Suggest from URL” control.
- [ ] Share flow UX (Courses/Articles): show inline “suggested vs edited” indicators so users can quickly trust/override autofilled values.
- [ ] Share flow validation (Courses/Articles): add live URL validation and duplicate checks before submit (existing URL/domain/title-provider hints) with actionable inline messages.
- [ ] Share flow reliability (Courses/Articles): persist unsent draft form state with autosave + recovery after refresh/navigation and explicit “discard draft” action.
- [ ] Share flow productivity (Courses/Articles): add one-click “apply all suggestions” and per-field “re-suggest” actions for faster curation.
- [ ] Share flow safety (Courses/Articles): provide “metadata unavailable” fallback UX with smart placeholders/examples so users can still submit quickly.
- [ ] Share flow post-submit: show contextual success summary (what was autofilled/saved) and quick follow-up actions (open item, copy link, add review/recommendation).
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
- [ ] Test reliability: isolate backend integration test auth/session state per test (or per module) to remove intermittent `401/404/500` flakiness.
- [x] Docs sync: update `docs/architecture_frontend.md` to match current IA/routes (`My learning`, `Insights`, mailbox activity) and current service/page boundaries.
- [ ] Docs sync: update `docs/architecture_backend.md` course/recommendation/review model details (`description`, `learning_outcomes`, `prerequisites`, `language`, `search_document`) and current service flows.

## Phase 12 — Analytics + Data Durability
- [ ] Colleague profiles with interest/completion tracking.
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
