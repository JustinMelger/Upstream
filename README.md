# Learning Hub

![coverage](docs/badges/coverage.svg)
![ci](https://github.com/JustinMelger/learning-platform/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue.svg)

A simple internal learning hub where colleagues can browse curated courses, track progress, and follow ordered learning paths.

## Docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Roadmap: [docs/roadmap.md](docs/roadmap.md)

## Run locally (Docker)
### Quick start
1. Build and start services:
   - `docker compose up --build`
2. Open the UI:
   - `http://localhost:8502`

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
   - `http://localhost:8502`

### Environment variables
- `SESSION_DAYS`: session lifetime in days (API).
- `BOOTSTRAP_ADMIN_USERNAME`: first admin username when no users exist (API).
- `BOOTSTRAP_ADMIN_PASSWORD`: first admin password when no users exist (API).
- `COOKIE_SECURE`: set to `true` behind HTTPS (UI).
- `DATABASE_URL`: Postgres connection string (API).

## Run locally (without Docker)
1. Install dependencies:
   - `uv sync --group dev`
2. Start the API:
   - `uvicorn backend.main:app --reload`
3. Start the UI (in a new terminal):
   - `streamlit run frontend/Home.py`
4. Open the UI:
    - `http://localhost:8501`

## Pages
- Home (Dashboard): progress snapshot, path progress, recent activity, featured paths, and recently added courses.
- Courses: browse + add/remove to My Courses (admins can edit/delete).
- My Courses: update status and remove tracked courses.
- Paths: browse and add to My Paths (admins can edit/delete and set order).
- My Paths: manage selected paths and update course status.
- Admin: create user accounts (admin only).

## Login (username + password)
- First login bootstraps an admin user (if no users exist yet) using the bootstrap credentials.
- Admins can create additional user accounts from the Dashboard.

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
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /courses`
- `GET /courses/{id}`
- `GET /paths`
- `GET /paths/{id}`
- `GET /tracking?colleague_id=...`
- `POST /tracking`
- `POST /tracking/delete`
- `GET /tracking/stats?colleague_id=...`
- `POST /paths/{id}/select`
- `POST /paths/{id}/unselect`

Admin-only:
- `POST /auth/users`
- `GET /auth/users`
- `POST /auth/users/reset`
- `POST /auth/users/disable`
- `DELETE /auth/users/{username}`
- `POST /courses`
- `PUT /courses/{id}`
- `DELETE /courses/{id}`
- `POST /paths`
- `PUT /paths/{id}`
- `DELETE /paths/{id}`
- `GET /tracking/stats` (team stats)
- `GET /tracking/stats/users` (team stats by user)

## Roles
- Admins can add/edit/delete courses and manage paths.
- Users can browse courses, manage My Courses, and manage My Paths.

## Tracking
- Set status per course: `interested`, `in_progress`, or `completed` (My Courses or My Paths).
- Remove a tracked course from My Courses if needed.

## Paths
- Create learning paths by selecting courses and ordering them (admin only).
- Add a path to My Paths from the Paths page.
- Update per-course status inside My Paths.
- Delete paths (admin only).

## Data
- Schema is managed via Alembic migrations (`just migrate`).
- The API starts with an empty database. Use the admin endpoints to create data.
