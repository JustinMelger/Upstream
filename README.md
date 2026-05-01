# Learning Hub

![coverage](docs/badges/coverage.svg)
![ci](https://github.com/JustinMelger/learning-platform/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue.svg)

Learning Hub is an internal learning platform for shared skill development.

At a glance:
- FastAPI backend APIs for auth, catalog, tracking, activity, and optional AI draft planning
- NiceGUI frontend for day-to-day learning workflows and team visibility
- Postgres persistence with Alembic migrations
- Optional local observability stack (OpenTelemetry, Prometheus, Tempo, Loki, Grafana)

Core workflows:
- Share courses, articles, videos, and mixed learning paths
- Track progress per user and across teams
- Review learning items and paths
- Use Teams as a lightweight workspace for membership, inbox, and team activity around globally visible shared content

## Docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Architecture & coding standards (one-pager): [docs/architecture_standards.md](docs/architecture_standards.md)
- V1 product spec: [docs/v1/README.md](docs/v1/README.md)
- Roadmap: [docs/roadmap.md](docs/roadmap.md)
- E2E notes: [tests/e2e/README.md](tests/e2e/README.md)

## Prerequisites
- Python 3.13
- `uv` for dependency/environment management
- `just` for local development commands
- Docker + Docker Compose (required for local Postgres and full containerized run)

## Choose a local setup
- Containerized app run: [Run locally (Docker)](#run-locally-docker)
- Local Python processes: [Run locally (without Docker)](#run-locally-without-docker)

## Run locally (Docker)
### Quick start
1. Start observability stack (separate deploy):
   - `docker compose -f docker-compose.observability.yml up -d`
2. Build and start app services (Postgres + API + UI):
   - `docker compose up --build`
3. Open the UI:
   - `http://localhost:8080`
4. API docs:
   - `http://localhost:8000/docs`

Notes:
- App stack (`docker-compose.yml`) and observability stack (`docker-compose.observability.yml`) are intentionally separate.
- App containers export OTLP to `host.docker.internal:4318`, so observability can run independently.

## Database migrations (Postgres)
When using Postgres, set `DATABASE_URL` and run:
- `just db-up`
- `just migrate`

Or run the full bootstrap flow:
- `just db-init` (starts Postgres, waits for readiness, applies latest migration)

### Live reload (Docker Compose watch)
1. Ensure Docker Compose supports `watch`:
   - `docker compose version`
2. Start observability stack:
   - `docker compose -f docker-compose.observability.yml up -d`
3. Start app services with file sync + reload:
   - `docker compose -f docker-compose.watch.yml watch`
4. Open the UI:
   - `http://localhost:8080`

## Run locally (without Docker)
1. Install dependencies:
   - `uv sync --group dev`
2. Start Postgres + migrate schema:
   - `just db-init`
3. Start the API:
   - `just backend`
4. Start the UI (in a new terminal):
   - `just ui`
5. Open the UI:
   - `http://localhost:8080`

Why this order:
- Backend expects a reachable Postgres database and current Alembic schema.
- `just db-init` avoids common first-run failures.

## Environment variables
API:
- `DATABASE_URL`: async Postgres connection string.
- `SESSION_DAYS`: session lifetime in days.
- `BOOTSTRAP_ADMIN_USERNAME`: first admin username when no users exist.
- `BOOTSTRAP_ADMIN_PASSWORD`: first admin password when no users exist.
- `FEATURE_TELEMETRY`: enable authenticated product telemetry ingestion (`0` or `1`, default `0`).
- `OTEL_ENABLED`: enable OpenTelemetry (`0` or `1`).
- `OTEL_SERVICE_NAME`: OpenTelemetry service name.
- `OTEL_SERVICE_VERSION`: service version label.
- `OTEL_DEPLOYMENT_ENVIRONMENT`: environment label (for example `dev`, `staging`, `prod`).
- `OTEL_TRACES_SAMPLE_RATIO`: trace sample ratio (`0.0` - `1.0`).
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`: OTLP HTTP traces endpoint.
- `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`: OTLP HTTP metrics endpoint.
- `OTEL_EXPORTER_OTLP_HEADERS`: optional comma-separated OTLP headers (`k=v,k2=v2`).

UI:
- `BACKEND_URL`: backend base URL used by NiceGUI frontend.
- `NICEGUI_STORAGE_SECRET`: secret used for NiceGUI per-user storage.
- `FEATURE_TELEMETRY`: enable frontend product telemetry emits (`0` or `1`, default `0`).
- `FEATURE_AI_CURATOR`: enable AI Curator page (`1` enabled, `0` disabled). Default is `0` for v1.
- `FEATURE_ARTICLES`: enable article-specific frontend features (`1` enabled, `0` disabled).

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

Typical dev loop:
- `just fmt`
- `just lint`
- Run focused tests (`just unit`, `just integration`, `just architecture`)
- Run full local quality gate before pushing: `just test`

Pull request checklist:
- Verify API/UI start locally
- Run relevant test targets
- Update docs if routes, commands, or env vars changed

## Development commands
- Format: `just fmt`
- Lint: `just lint`
- Lint ratchet + strict core quality gate: `just lint-ratchet`
- Unit tests: `just unit`
- Integration tests: `just integration`
- Architecture tests: `just architecture`
- Full local gate: `just test`
- Frontend architecture guards: `just frontend-arch-guards`
- Architecture docs sync guard: `just architecture-sync-check`

Optional local commit hooks:
- Install: `uv run pre-commit install`
- Run on all files: `uv run pre-commit run --all-files`

## Pages
- Home/Insights (`/` and `/home`): team-level progress and contribution visibility.
- Explore (`/explore`): unified global catalog for courses, paths, articles, and videos.
- Explore detail routes:
  - `/explore/courses/{course_id}`
  - `/explore/paths/{path_id}`
  - `/explore/articles/{article_id}`
- Teams (`/teams`): basic workspace for membership, inbox, and team activity.
- Profile (`/profile`, `/profile/stats`): personal account and stats views.
- AI Curator (`/ai`): goal-driven draft plan workflow (feature-flagged, off by default for v1).
- Admin (`/admin/users`): user management (admin only).

Navigation note:
- The “Menu” dropdown in the header is the canonical in-app navigation surface.

## Login (username + password)
- First login bootstraps an admin user (if no users exist yet) using the bootstrap credentials.
- Admins can create additional user accounts from the Admin page.

## Feature snapshot
- Social learning flows: share and review learning items and paths.
- Team activity and mailbox view within a basic Teams workspace.
- Explore-first content workflow (courses, paths, articles, videos) with global catalog visibility.
- Optional AI draft planner endpoint (`POST /ai/plan`) kept out of the core v1 narrative.

Visibility model in v1:
- shared learning items and paths are globally visible in `Explore`
- Teams provide a focused activity and follow-up workspace
- Teams do not create private catalog silos in v1

## Conventional commits
Use Conventional Commits for automated release notes.

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

## API quick reference
- `GET /health`
- `POST /telemetry/events` (authenticated frontend product events sink; feature-flagged)

Endpoint families:
- Auth/session: `/auth/*`
- Courses (+ reviews): `/courses/*`
- Paths (+ select/status + reviews): `/paths/*`
- Articles (+ reviews): `/articles/*`
- Videos (+ reviews): `/videos/*`
- Tracking/stats: `/tracking/*`
- Notifications/activity: `/notifications/*`
- Teams/activity context: `/teams/*`
- URL preview metadata: `/url-preview/*`
- Telemetry/events: `/telemetry/*` (feature-flagged)
- AI draft planning: `/ai/*` (feature-flagged)

## Observability (OpenTelemetry + Prometheus + Grafana)
- Start observability independently:
  - `docker compose -f docker-compose.observability.yml up -d`
- Observability stack includes:
  - OpenTelemetry Collector on `4317`/`4318`
  - Tempo on `http://localhost:3200` (trace backend)
  - Loki on `http://localhost:3100` (log backend)
  - Promtail (ships Docker logs to Loki)
  - Prometheus on `http://localhost:9090`
  - Grafana on `http://localhost:3000` (default `admin` / `admin`)
  - Collector Prometheus metrics endpoint on `http://localhost:9464/metrics`
- API exports traces + metrics via OTLP HTTP to Collector.
  - App containers send OTLP to `host.docker.internal:4318`, so observability can run in a separate Compose project.
- Collector config lives at:
  - `deploy/observability/otel-collector-config.yaml`
  - `deploy/observability/prometheus.yml`
  - `deploy/observability/tempo.yaml`
  - `deploy/observability/loki-config.yaml`
  - `deploy/observability/promtail-config.yaml`
  - `deploy/observability/grafana/provisioning/datasources/datasources.yml`
  - `deploy/observability/grafana/provisioning/dashboards/dashboards.yml`
  - `deploy/observability/grafana/provisioning/dashboards/json/learning-platform-observability.json`
- Collector trace export target env vars (in observability compose):
  - `TEMPO_OTLP_ENDPOINT` (default `http://tempo:4318/v1/traces`)
  - `TEMPO_OTLP_AUTH_HEADER` (optional)
- Grafana auto-loads the starter dashboard:
  - `Learning Platform Observability`

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
- Tracking is managed from Explore course/path views and dashboard-oriented pages.

## Paths
- Create learning paths by selecting courses and ordering them.
- Select paths from Explore or related UI flows.
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
FEATURE_AI_CURATOR=0
FEATURE_ARTICLES=1
```

## Troubleshooting
- Migrations fail / schema mismatch:
  - Run `just db-init` (or `just db-up` + `just migrate`).
- UI cannot reach API:
  - Verify backend is on `http://127.0.0.1:8000` and `BACKEND_URL` matches.
- Login bootstrap not working:
  - Ensure database is empty and bootstrap env vars are set.
- Port conflict:
  - Check/stop processes on ports `8000` (API), `8080` (UI), and `5432` (Postgres).

## Production notes
- Use a managed Postgres instance and run Alembic migrations during deploy.
- Keep secrets in environment/secret manager (never commit credentials).
- Disable bootstrap admin credentials after initial setup.
