# Operations and verification

## Production configuration

Set `ENVIRONMENT=production`, `PUBLIC_ORIGIN=https://your-host`, a random `BROWSER_SECRET` of at least 32 characters, and explicit bootstrap credentials. Compose sets `API_ROOT_PATH=/api` so API documentation resolves through Nginx. Terminate TLS at your ingress and send traffic to Nginx's port 8080. Production startup rejects insecure defaults; session cookies are HttpOnly, Secure, and SameSite=Lax.

Browser authentication uses `/api/auth/browser/login`, `/session`, and `/logout`. Session responses contain a CSRF token, never the session credential. Mutations require the configured Origin and `X-CSRF-Token`. Header authentication remains for one rollback release; an explicit header never falls back to cookies. Logout revokes only the presented session. Password reset and disabling an account revoke all its sessions.

The API and migration containers run as UID/GID `10001:10001`. The UI runs as the image's `nginx` user on port 8080, with PID and temporary files under `/tmp`. Both images use separate build and runtime stages. The API runtime includes only its virtual environment, backend code and Alembic files; development scripts and frontend sources are excluded.

Both Dockerfiles use the repository root as their build context. To build the API image directly, run `docker build -f backend/Dockerfile -t upstream-api:local .` from the repository root. Compose and CI use the same Dockerfile.

## Published images

Releases publish `ghcr.io/<owner>/upstream-api` and `ghcr.io/<owner>/upstream-ui`. Stable releases provide exact version, minor, major and `latest` tags; release candidates provide their release tag and `rc`. Prefer the same exact version for both images in a deployment. Release tags continue to use `v…`; package renaming does not reset version history.

Local Compose builds use `upstream-api:local` (API and migration service) and `upstream-ui:local`. To deploy published images, set `API_IMAGE` and `UI_IMAGE` to the fully qualified release references in the deployment environment, authenticate to GHCR if necessary, then run:

```sh
docker compose pull
docker compose up -d --no-build
```

The migration service uses the same API image. Preserve existing project names, database credentials and volumes. Previously published `learning-platform` and `learning-platform-ui` images are not deleted or retagged by this change; retain their exact references for rollback. Future releases publish under the Upstream names, so deployments consuming the old names must update both references.

## Routes

`/home`, `/explore`, `/explore/courses/:id`, `/explore/articles/:id`, `/explore/videos/:id`, `/explore/paths/:id`, `/share/item`, `/share/path`, `/activity`, `/profile`, `/admin/users`, `/login`.

`/teams` redirects to Activity with a retirement notice. `/profile/stats` redirects to Activity's personal statistics. Existing content and review deep links remain valid. Missing API routes return JSON errors rather than React HTML.

## API contracts

Backend paths below are exposed under `/api` by Nginx/Vite:

- `/catalog`: unified catalog; search/type/provider/category/author filters and newest/title/rating sorts.
- `/catalog/facets`: authenticated, searchable provider/category options within active catalog filters.
- `/learning/summary`: personal totals and next course.
- `/learning/items`: tracked courses, selected paths with personal course totals, or contributions.
- `/learning/paths/:id`: personal course-only path progress and selection state.
- `/activity`: personal review updates or shared-content events.
- Content detail, sharing, review, course tracking, and account endpoints remain supported. Header authentication remains available for the rollback window.

The bounded workspace reads above replace the retired unbounded content lists, batch review summaries, selected-path list, and tracking/statistics reads. Content detail and mutation routes remain supported. Retired reads are no longer part of the public API contract.

Paginated reads return `{items, total, page, page_size}`; default page size is 24 and maximum is 100. Articles and videos support owner/admin `PUT` and `DELETE`. Deletion removes reviews and path references without deleting the path. Recommendation notes are plain text, nullable, and limited to 1,000 characters; omitted update fields preserve the note and null clears it.

New resource forms offer explicit, optional Fetch details for page-authored title, description, and provider suggestions. Manual sharing never requires external metadata requests. Image/classification compatibility response fields remain empty. See the [product guide](product.md#sharing-and-reviews) and [backend architecture](architecture_backend.md#metadata-and-schema-compatibility) for form behavior and fetching safeguards. Undated historical paths are not assigned invented share dates.

Regenerate types after API changes:

```sh
uv run python -m scripts.export_openapi
npm run api:generate --prefix frontend/react
```

Commit both `frontend/react/openapi.json` and its generated TypeScript types. CI checks drift.

Rollback uses retained React UI and backend image versions. NiceGUI rollback images are no longer retained. Header authentication and team tables remain available during their separate compatibility window.

## Tests and quality checks

Dependency audits run in the separate `dependency-audit` workflow daily at 06:23 UTC (08:23 Amsterdam summer time, 07:23 winter time), with a manual Actions trigger. Scheduled runs use the default branch, so the schedule takes effect after merge. Backend and frontend audits run independently; frontend findings at moderate severity or higher fail its job. Pull-request and main-push CI no longer include the dedicated audit steps. Local `just audit` and `just test` retain their audit checks.

**Use a disposable PostgreSQL database. Backend fixtures truncate its tables. Never point tests at your working application database.**

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy backend
uv run lint-imports
uv run pip-audit
uv run python -m scripts.export_openapi --check
uv run pytest tests/backend
npm run format:check --prefix frontend/react
npm run lint --prefix frontend/react
npm run typecheck --prefix frontend/react
npm run test --prefix frontend/react
npm run build --prefix frontend/react
npm audit --audit-level=moderate --prefix frontend/react
```

For browser tests, create a separate empty database whose name ends in `_test`, export its `DATABASE_URL`, migrate it, then seed it explicitly:

```sh
E2E_DATABASE_IS_DISPOSABLE=1 uv run python -m scripts.seed_react_demo
npm exec --prefix frontend/react -- playwright install chromium
npm run e2e --prefix frontend/react
```

The seed command refuses non-test databases and databases with existing users. Browser tests start their own backend on 18000 and Vite on 15173. Demo credentials exist only in that disposable dataset: `alex / learn-demo-123` and `admin / admin`.

## Visual regression checks

Reviewed baselines live in `frontend/react/tests/visual/baselines`. The pinned Linux Playwright image keeps local and CI rendering consistent. Tests mock only API responses, use local fonts, and cover My learning, Explore, Activity, detail, sharing, artwork fallback, empty, loading, and error states at 390px, 768px, and 1440px.

```sh
docker build -t learning-visual -f frontend/react/Dockerfile.visual frontend/react
docker run --rm --ipc=host learning-visual
```

Generate committed baselines only in this pinned Linux container. Native macOS and Windows runs can render fonts and line wrapping differently, even with the same browser version and bundled fonts; their passing screenshots are not CI-compatible baselines.

For an intentional design change, generate candidates with a writable baseline mount, inspect every changed PNG, and include the reviewed changes in the PR:

```sh
docker run --rm --ipc=host \
  -v "$PWD/frontend/react/tests/visual/baselines:/app/tests/visual/baselines" \
  learning-visual npm run test:visual -- --update-snapshots=all
```

After reviewing the candidates, rebuild the image so it contains the updated baselines, then run the normal comparison without snapshot updates:

```sh
docker build -t learning-visual -f frontend/react/Dockerfile.visual frontend/react
docker run --rm --ipc=host \
  -v "$PWD/frontend/react/test-results:/app/test-results" \
  learning-visual
```

CI compares baselines without updating them and uploads differences on failure. Browser package/image upgrades must be made together and their baseline differences reviewed.

## Release and rollback

Retain compatible previous application images and a recoverable database backup before deploying. Rebuild API and UI images after source changes; restarting an old image does not refresh its contents. Preserve PostgreSQL volumes, and never seed a working application database.

Header authentication and retained team tables remain protected during the rollback window. The repository does not establish that this window has closed. Do not remove the compatibility transport, drop retained tables or edit historical migrations until retirement is explicitly authorized. Restoring older application images requires a compatible schema; do not pair an image rollback with destructive schema changes. New nullable content fields should survive an image rollback.

## Optional observability

Backend OpenTelemetry is disabled by default. Enable it only with independently configured OTLP trace and metric endpoints; the repository does not bundle a monitoring stack or expose a product-event ingestion endpoint. See [backend architecture](architecture_backend.md#deployment-and-observability).

## Task shortcuts

Use `just lint`, `just unit`, `just integration`, `just architecture`, `just audit` and `just build-ui` for grouped checks. `just quality` combines lint and import contracts. `just api-types` regenerates both contracts; `just architecture-sync-check` checks drift. `just build-images` builds the Compose images. The old `build` and `lint-ratchet` names remain compatibility aliases.

`just unit`, `just integration`, `just test`, `just check` and `just e2e` require `E2E_DATABASE_IS_DISPOSABLE=1` and an explicit PostgreSQL `DATABASE_URL` whose database name ends in `_test`. This acknowledgement does not create or isolate a database: provision a disposable database first. Never use retained application data. The guard applies to just recipes; direct pytest commands still require the same care.

`just visual` runs the pinned Linux screenshot comparison and saves failure artifacts in `frontend/react/test-results`. `just check` combines backend/frontend checks, contract consistency, the production UI build and visual checks. Run `just e2e` separately against a migrated and seeded disposable browser database using the preparation steps above; backend tests can truncate seed data.
