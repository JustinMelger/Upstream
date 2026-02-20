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
- [ ] Frontend architecture alignment: add `admin_users_service.py` and `ai_curator_service.py` to keep page modules focused on UI composition/event binding.
- [x] Frontend clean code: enforce page boundary (pages = UI composition/event binding; move API orchestration to services/use-cases).
- [ ] Frontend clean code: introduce typed page state/view-model objects to reduce large closure state (`nonlocal`) usage.
- [ ] Frontend clean code: extract large nested handlers into domain action modules (`learning_actions`, `courses_actions`, `paths_actions`).
- [ ] Frontend clean code: componentize repeated page sections (top bar, filter rail, card sections, load-more footer).
- [ ] Frontend clean code: reduce page-module size/complexity (`courses.py`, `paths.py`, `learning.py`) by splitting into focused UI sections and action modules.
- [ ] Frontend clean code: centralize deep-link and intent navigation logic in a shared navigation helper.
- [ ] Frontend clean code: standardize mutation flow (optimistic update + rollback + notification + targeted refresh) across pages.
- [ ] Frontend clean code: add lightweight page-state reducers/helpers to tame `nonlocal` sprawl and make state transitions explicit/testable.
- [ ] Frontend clean code: increase service/use-case unit tests to cover extracted orchestration logic.
- [ ] Performance polish: avoid full list reloads after small actions (optimistic UI updates for tracking/reviews), parallelize detail fetches, and add lightweight caching for `/courses/{id}` and reviews.

## Phase 11 — Operability + Quality
- [ ] Activity feed UX v2: add filters (`All`, `Recommendations`, `Ratings`, `Courses`, `Paths`, `Articles`).
- [ ] Activity feed UX v2: add unread state + mailbox badge + “Mark all read”.
- [ ] Activity feed UX v2: add relative timestamps with absolute time on hover.
- [ ] Activity feed UX v2: add pagination/“Load more” for older events.
- [ ] Activity feed UX v2: improve article deep-linking to open the specific item context.
- [ ] Activity feed UX v2: group burst events and rank high-signal events higher (e.g., ratings on your shared content).
- [ ] Observability: add frontend telemetry for core actions (share/select/review/complete) and page-level error tracking.
- [ ] Notification resilience hardening: enrich `safe_notify` logs with action/page context, add optional strict mode for dev/test, and add regression tests for deleted-slot notification paths.
- [ ] Accessibility pass: keyboard navigation, visible focus states, ARIA labels for icon-only actions, and contrast audit fixes.
- [ ] Resilience UX: network/offline banner, retry affordances, and standardized section-level error states.
- [ ] Performance: short-TTL client caching for hot reads (`/tracking`, review summaries), batched detail fetches, and fewer full reloads after mutations.
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
