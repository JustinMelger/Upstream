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

## Phase 6 — Colleague tracking + analytics
- [ ] Colleague profiles with interest/completion tracking.
- [ ] Basic analytics (popular courses, completion rates).

## Phase 7 — Data durability + polish
- [ ] Import/export tools for course data.
- [ ] UI polish + accessibility improvements.

## Phase 8 — AI Curation (optional)
- [ ] Add an “AI Curator” backend service that turns a user goal into a proposed learning plan (draft path + ordered draft courses).
- [ ] Implement “suggest then approve”: UI preview with edit/remove/reorder before persisting.
- [ ] Add course discovery step (start with constrained sources) and normalize results to the course schema.
- [ ] Add de-duplication heuristics (URL-based + provider/title similarity).
- [ ] Add provenance fields for AI-suggested content (e.g. `source`, `source_url`, `confidence`) and surface them in UI.
- [ ] Run discovery as a background job (avoid blocking request/response; show progress + retries).
- [ ] Persist approved drafts via existing domain services (`CoursesService`, `PathsService`, `TrackingService`) to keep consistency.

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
- [ ] Courses UX: paginate or add “Load more”/infinite scroll for large catalogs.
- [x] Courses UX: enhance empty states (show active filters + single “Reset all” CTA; “Share the first course” for empty catalog).
- [ ] Courses UX: add facet counts for provider/category/status options.
- [x] Courses UX: paginate or add “Load more”/infinite scroll for large catalogs.
- [ ] Courses UX: polish card actions (status as clearer control; optional “Copy link” quick action).
- [ ] Courses UX: highlight “new/updated” courses and add a “Recently added” sort.


## Phase 10 — Social Layer (By Colleagues, For Colleagues)
- [ ] Add recommendations for courses/paths (who recommended + optional note + timestamp).
- [x] Add reviews for courses (rating + text) with basic moderation/admin removal.
- [ ] Add reviews for paths (text) with basic moderation/admin removal.
- [ ] Add reviews for articles (rating + text) with basic moderation/admin removal.
- [x] Surface social signals in UI (Home + course/path details).
- [ ] Performance polish: avoid full list reloads after small actions (optimistic UI updates for tracking/reviews), parallelize detail fetches, and add lightweight caching for `/courses/{id}` and reviews.
- [ ] Add “Suggest a course/path” drafts (user-submitted) with admin approve/edit → canonical content.
- [ ] Basic de-duplication for suggested courses (URL-based + title/provider similarity).
- [ ] Notifications v1 (optional): show “recommended to you” inbox or activity feed (no email).
- [ ] Course content description: add `courses.description` (short summary) and surface it across UI; keep `level` optional and de-emphasize (hide behind “more filters”) before deciding to drop it.
- [ ] AI-ready metadata: add/standardize course content fields (`description`, optional `learning_outcomes`, `prerequisites`, `language`) and define a derived “search document” that combines course + review text for later AI search/planning.
- [x] Ownership + permissions: allow any authenticated user to create courses/paths; only the creator (or admin) can edit/delete; admin can edit/delete everything.
- [ ] Copy/wording shift: change UI labels from admin CRUD (“New course/path”) to social contribution (“Share course/path”) once ownership/permissions is live.
