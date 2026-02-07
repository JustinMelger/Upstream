# Roadmap

## Phase 1 — MVP catalog
- Status: Done
- Stable data model for courses (CSV-based seed).
- Search + filter UI.
- One-click course links.
- Basic “Add course” form for curators.

## Phase 2 — Management + paths
- Status: Done
- Edit/delete courses.
- Learning paths with ordered sequences.
- Path overview page with progress per path.

## Phase 3 — Auth v1 (self-hosted + optional OAuth)
- Status: Done (self-hosted)
- API routes: `/auth/login`, `/auth/me`, `/auth/logout`, `/auth/role`, and admin user management under `/auth/users`.
- Session storage: server-side sessions keyed by `X-Session-Token` (frontend stores token in a cookie).
- Bootstrap admin: first login can create the initial admin when no users exist (env-controlled).
- UI: login screen + guarded pages.

## Phase 3b — Auth enhancements (optional)
- Invite-code login (email + code).
- OAuth configuration (Google/Microsoft/Okta) via env vars.
- Admin allowlist (post-auth).

## Phase 4 — Postgres + Async SQLAlchemy + Alembic
1. Switch infra to Postgres immediately by running a local `postgres` container in `docker-compose.yml` and `docker-compose.watch.yml`, and standardize on `DATABASE_URL` for the app (keep `DATABASE_PATH` only as a temporary fallback during the cutover).
2. Use the “session-per-request” pattern for FastAPI + async SQLAlchemy: add `backend/database/session.py` (engine + `async_sessionmaker` + `get_session()` dependency) and make repositories async and constructed per-request from the current `AsyncSession` (avoid global service singletons once sessions are introduced).
3. Add Alembic and generate an initial migration matching the current schema (users/sessions/courses/paths/path_courses/user_paths/tracking), then enforce migrations in CI and on startup (remove ad-hoc `ALTER TABLE` from `init_db()` once migrated).
4. Migrate incrementally: `courses` first, then `paths` + `path_courses` (transactions), then `tracking`, and finally `auth` + `sessions`.
5. Move API integration tests to `httpx.AsyncClient` + `pytest-anyio`, and run migrations against a Postgres service in CI before running tests.
6. Next concrete steps (suggested order): add `backend/database/session.py` with async engine/session factory + `get_session()`, add Alembic (`alembic/`, `alembic.ini`) and an initial migration + a `just migrate` + CI migration step, migrate the `courses` domain end-to-end to async SQLAlchemy as the template, and then switch integration tests from `TestClient` to `httpx.AsyncClient` using `pytest-anyio`.
7. Data + ops details to include in the migration plan: one-time idempotent data migration from `learning_hub.db` (and `courses.csv`) into Postgres, replace global service singletons (`*_service = ...`) with per-request construction from `AsyncSession` in `backend/api/deps.py` (and move routers to `async def`), add dependencies + `just db-up`/`just migrate`/`just seed`, update CI to run Postgres + `alembic upgrade head` before tests, decide a Postgres seeding strategy (prefer a dedicated seed step over app startup), set operational defaults (pool sizing/timeouts) and safe migration execution, and update `README.md`/`docs/architecture.md` after cutover.

## Phase 5 — UI migration to NiceGUI
- Create NiceGUI shell app with shared navigation and layout.
- Port login/session flow to NiceGUI (reuse backend auth).
- Port core pages: Home/Dashboard, Courses, My Courses.
- Port Paths + My Paths (including ordering UI and admin edit flows).
- Parity check + remove Streamlit UI once stable.

## Phase 6 — Colleague tracking + analytics
- Colleague profiles with interest/completion tracking.
- Basic analytics (popular courses, completion rates).

## Phase 7 — Data durability + polish
- Import/export tools for course data.
- UI polish + accessibility improvements.
