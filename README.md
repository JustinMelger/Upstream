# Learning Hub

![coverage](docs/badges/coverage.svg)
![ci](https://github.com/JustinMelger/learning-platform/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue.svg)

A simple internal learning hub where colleagues can browse curated courses, track progress, and follow ordered learning paths.

## Docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Architecture & coding standards (one-pager): [docs/architecture_standards.md](docs/architecture_standards.md)
- Roadmap: [docs/roadmap.md](docs/roadmap.md)

## Prerequisites
- Python 3.13
- `uv`
- `just`
- Docker + Docker Compose (for local Postgres / containerized run)

## Run locally (Docker)
### Quick start
1. Build and start services:
   - `docker compose up --build`
2. Open the UI:
   - `http://localhost:8080`

## Database migrations (Postgres)
When using Postgres (Phase 4), set `DATABASE_URL` and run:
- `just db-up`
- `just migrate`

### Live reload (Docker Compose watch)
1. Ensure Docker Compose supports `watch`:
   - `docker compose version`
2. Start services with file sync + reload:
   - `docker compose -f docker-compose.watch.yml watch`
3. Open the UI:
   - `http://localhost:8080`

### Environment variables
- `SESSION_DAYS`: session lifetime in days (API).
- `BOOTSTRAP_ADMIN_USERNAME`: first admin username when no users exist (API).
- `BOOTSTRAP_ADMIN_PASSWORD`: first admin password when no users exist (API).
- `NICEGUI_STORAGE_SECRET`: secret used for NiceGUI per-user storage (UI).
- `DATABASE_URL`: Postgres connection string (API).

## Run locally (without Docker)
1. Install dependencies:
   - `uv sync --group dev`
2. Start the API:
   - `just backend`
3. Start the UI (in a new terminal):
   - `just ui`
4. Open the UI:
   - `http://localhost:8080`

## Contributor quick start
1. Install dependencies:
   - `uv sync --group dev`
2. Start Postgres + migrate:
   - `just db-init`
3. Start backend:
   - `just backend`
4. Start UI (new terminal):
   - `just ui`

Optional:
- Start backend + UI together after DB init: `just dev`

## Development commands
- Format: `just fmt`
- Lint: `just lint`
- Unit tests: `just unit`
- Integration tests: `just integration`
- Architecture tests: `just architecture`
- Full local gate: `just test`
- Frontend architecture guards: `just frontend-arch-guards`
- Architecture docs sync guard: `just architecture-sync-check`

## Pages
- Insights (`/insights`): team-level progress and contribution visibility.
- My learning (`/learning`): personal execution view (tracked/selected/recommended/shared items).
- Activity (`/activity`): mailbox-style activity feed (personal + team activity tab).
- Courses (`/courses`): browse/share/review/recommend courses and manage tracking status.
- Paths (`/paths`): browse/share/select/review/recommend paths and update path status.
- Articles (`/articles`): share and review knowledge links.
- Admin (`/admin/users`): user management (admin only).

## Login (username + password)
- First login bootstraps an admin user (if no users exist yet) using the bootstrap credentials.
- Admins can create additional user accounts from the Admin page.

## Feature snapshot
- Social learning flows: share/review/recommend courses and paths.
- Activity mailbox and team activity view.
- My learning execution view (`Learning` and `Shared` tabs).
- AI draft planner endpoint (`POST /ai/plan`) for proposed learning plans.

## Conventional commits
We use Conventional Commits for automated release notes.

Format:
`type(scope): description`

Common types:
- `feat`: new feature
- `fix`: bug fix
- `chore`: tooling or maintenance
- `docs`: documentation changes
- `refactor`: code change without behavior change

Examples:
- `feat(paths): add course ordering`
- `fix(tracking): prevent empty status save`
- `chore: add semantic-release config`

## API endpoints (read-first)
- `GET /health`

Endpoint families:
- Auth/session: `/auth/*`
- Courses (+ reviews/recommendations): `/courses/*`
- Paths (+ select/status + reviews/recommendations): `/paths/*`
- Articles (+ reviews): `/articles/*`
- Tracking/stats: `/tracking/*`
- Notifications/activity: `/notifications/*`
- AI draft planning: `/ai/*`

OpenAPI docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Admin-only:
- `POST /auth/users`
- `GET /auth/users`
- `POST /auth/users/reset`
- `POST /auth/users/disable`
- `DELETE /auth/users/{username}`
- `GET /tracking/stats` (team stats)
- `GET /tracking/stats/users` (team stats by user)

Owner/admin-only (creator or admin):
- `PUT /courses/{id}`
- `DELETE /courses/{id}`
- `PUT /paths/{id}`
- `DELETE /paths/{id}`

## Roles
- Admins can create/edit/delete any courses and paths, and manage users.
- Users can create courses and paths; they can edit/delete only the ones they created.

## Tracking
- Set status per course: `interested`, `in_progress`, or `completed`.
- Tracking is managed from `Courses`, `Paths` details, and `My learning`.

## Paths
- Create learning paths by selecting courses and ordering them.
- Select a path from the Paths page.
- Update per-path status (`not_selected`, `selected`, `completed`) and per-course tracking status.
- Delete paths you created (admins can delete any).

## Data
- Schema is managed via Alembic migrations (`just migrate`).
- The API starts with an empty database. Use the admin endpoints to create data.

## Example `.env`
```env
DATABASE_URL=postgresql+asyncpg://learning_platform:learning_platform@127.0.0.1:5432/learning_platform
BACKEND_URL=http://127.0.0.1:8000
SESSION_DAYS=7
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=change-me
NICEGUI_STORAGE_SECRET=change-me-too
```

## Troubleshooting
- Migrations fail / schema mismatch:
  - Run `just db-init` (or `just db-up` + `just migrate`).
- UI cannot reach API:
  - Verify backend is on `http://127.0.0.1:8000` and `BACKEND_URL` matches.
- Login bootstrap not working:
  - Ensure database is empty and bootstrap env vars are set.
- Port conflict:
  - Check/stop processes on ports `8000` (API) and `8080` (UI).

## Production notes
- Use a managed Postgres instance and run Alembic migrations during deploy.
- Keep secrets in environment/secret manager (never commit credentials).
- Disable bootstrap admin credentials after initial setup.
