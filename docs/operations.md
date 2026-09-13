# Operations and verification

## Production configuration

Set `ENVIRONMENT=production`, `PUBLIC_ORIGIN=https://your-host`, a random `BROWSER_SECRET` of at least 32 characters, and explicit bootstrap credentials. Compose sets `API_ROOT_PATH=/api` so API documentation resolves through Nginx. Terminate TLS at your ingress and send traffic to Nginx's port 8080. Production startup rejects insecure defaults; session cookies are HttpOnly, Secure, and SameSite=Lax.

Browser authentication uses `/api/auth/browser/login`, `/session`, and `/logout`. Session responses contain a CSRF token, never the session credential. Mutations require the configured Origin and `X-CSRF-Token`. Header authentication remains for one rollback release; an explicit header never falls back to cookies. Logout revokes only the presented session. Password reset and disabling an account revoke all its sessions.

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
- Existing `/courses`, `/articles`, `/videos`, `/paths`, review, tracking, and account endpoints.

Paginated reads return `{items, total, page, page_size}`; default page size is 24 and maximum is 100. Articles and videos now support owner/admin `PUT` and `DELETE`. Deletion removes reviews and path references without deleting the path. Recommendation notes are plain text, nullable, and limited to 1,000 characters; omitted update fields preserve the note and null clears it.

New resource forms offer explicit, optional Fetch details for page-authored title, description, and provider suggestions. Manual sharing never requires external metadata requests. External-image fetching and classification inference have been removed; compatibility response fields remain empty. See [metadata autofill](metadata_autofill_implementation.md) for behavior and fetching safeguards. Undated historical paths are not assigned invented share dates.

Regenerate types after API changes:

```sh
uv run python -m scripts.export_openapi
npm run api:generate --prefix frontend/react
```

Commit both `frontend/react/openapi.json` and its generated TypeScript types. CI checks drift.

## Tests and quality checks

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

Keep the previous NiceGUI image and header authentication available for one release cycle. React is the supported UI and cutover is complete. The removed external-image fetcher is not needed when rolling back to prior images. Team tables remain intact for rollback; no team-data destruction occurs in this release. Do not restore the old frontend while simultaneously running a future migration that drops its required tables.

The repository does not bundle an observability Compose stack. Backend OpenTelemetry remains optional and requires an independently configured OTLP endpoint. See [React implementation record](react_redesign_plan.md), [frontend architecture](architecture_frontend.md), and [backend architecture](architecture_backend.md).


Use `just lint`, `just unit`, `just integration`, `just architecture`, `just audit`, and `just build` for the equivalent grouped checks. `just api-types` regenerates both contracts; compare generated files to detect drift.

The standard Docker address is `http://localhost:8080`. The existing developer preview at `http://localhost:18080` uses a separate Compose project; it is not the installation default. Rebuild images before refreshing a preview, tag both previous images for rollback, and preserve its PostgreSQL volume. Never run seed scripts against preview data.
