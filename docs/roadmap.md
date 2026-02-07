# Roadmap

## Phase 1 — MVP catalog
- [x] Stable data model for courses (CSV-based seed).
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
- [ ] Update CI to run migrations (Postgres service + `alembic upgrade head`) before tests.
- [ ] Migrate incrementally: `courses` first, then `paths` + `path_courses`, then `tracking`, then `auth` + `sessions`.
- [ ] Move API integration tests to `httpx.AsyncClient` + `pytest-anyio`.
- [ ] One-time idempotent data migration from `learning_hub.db` (and `courses.csv`) into Postgres.
- [ ] Replace global service singletons (`*_service = ...`) with per-request construction from `AsyncSession` in `backend/api/deps.py` (and move routers to `async def`).
- [ ] Decide Postgres seeding strategy (prefer a dedicated seed step over app startup).
- [ ] Add operational defaults (pool sizing/timeouts) and safe migration execution (avoid concurrent migration runs).
- [x] Regenerate and commit `uv.lock` after dependency changes (keep CI/Docker `uv sync --frozen` working).

## Phase 5 — UI migration to NiceGUI
- [ ] Create NiceGUI shell app with shared navigation and layout.
- [ ] Port login/session flow to NiceGUI (reuse backend auth).
- [ ] Port core pages: Home/Dashboard, Courses, My Courses.
- [ ] Port Paths + My Paths (including ordering UI and admin edit flows).
- [ ] Parity check + remove Streamlit UI once stable.

## Phase 6 — Colleague tracking + analytics
- [ ] Colleague profiles with interest/completion tracking.
- [ ] Basic analytics (popular courses, completion rates).

## Phase 7 — Data durability + polish
- [ ] Import/export tools for course data.
- [ ] UI polish + accessibility improvements.
