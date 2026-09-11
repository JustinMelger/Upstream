# Backend architecture

FastAPI serves the shared content library, accounts, reviews, and personal learning state. PostgreSQL remains the source of truth; Alembic owns schema changes.

## Request flow

Browser → Nginx `/api` proxy → authentication/CSRF middleware → router → service → async repository → PostgreSQL.

Routers validate transport contracts and enforce authentication/ownership. Services implement domain rules. Repositories own SQL, with request-scoped commit/rollback. Import-linter prevents services from depending on API modules and repositories from depending on services or API modules.

## Authentication

`browser_security.py` adapts an HttpOnly cookie to the existing session boundary only after checking mutation Origin and a session-bound CSRF token. An explicit `X-Session-Token` header always takes precedence and never falls back to a cookie. Browser session responses expose account metadata and CSRF tokens, never the session credential. Production requires HTTPS and explicit secrets.

Session validation checks expiration, user existence, and enabled status. Logout revokes only the current session; reset and account disable revoke all affected sessions. Header transport is retained for the one-release rollback window.

## Content and learning

Courses, articles, videos, and paths retain their IDs, authors, reviews, and existing progress. All support recommendation notes. Owner/admin edits and deletion are supported across content types. Article/video/course deletion removes polymorphic path references transactionally; remaining order and the path itself are preserved.

Tracking applies only to courses. Path selection and manual status remain independent of the course-completion count.

`WorkspaceRepository` provides SQL read projections for `/catalog`, `/catalog/facets`, `/learning/summary`, `/learning/items`, `/learning/paths/{id}`, and `/activity`. Catalog and activity merge content types before stable sorting and pagination. Page sizes default to 24 and are capped at 100. Query counts remain bounded as catalog size grows; no per-item HTTP fan-out is required for My learning or Activity.

Activity projects existing content shares and reviews. Personal scope contains others' reviews on the user's own content; shared scope contains global shares/reviews. Neither exposes other people's course tracking. Statistics are self-only for members; aggregate/per-user administrative statistics require admin access.

## Migrations and retirement

Migration `20260909_0018` adds nullable recommendation notes and a nullable path creation timestamp with a default for future records. Existing undated paths keep null timestamps and are excluded from newly-shared events. The populated migration verifier compares every original field across 14 legacy tables.

Teams, AI Curator, and legacy notification routes are unregistered. The authenticated `/url-preview/metadata` route serves explicit Fetch details. Tracking has no Teams dependency. Team tables remain during rollback, with historical migrations unchanged. Metadata-only fetching validates and pins public destinations, bounds redirects/time/content/concurrency/cache, and never runs on content reads. External-cover fetching and inferred classification helpers have been removed; response compatibility fields remain empty.

## Deployment and observability

The API image contains Python runtime dependencies only. Nginx serves the React assets and proxies `/api`; `API_ROOT_PATH=/api` keeps API documentation links correct. The migration container completes before API startup. React's Vite server proxies `/api` during development.

OpenTelemetry instrumentation and the optional Collector/Tempo/Prometheus/Loki/Grafana stack remain available. Optional authenticated `/telemetry/events` ingestion requires `FEATURE_TELEMETRY=1`; the new React UI does not require it.

See [React implementation record](react_redesign_plan.md) and [README](../README.md) for release gates, setup, and rollback.

The UX refinement adds paginated provider/category facets using the catalog's active filters except the selected facet itself. Personal learning items optionally include `course_progress` for selected paths, computed in one extra SQL query for the bounded page. Catalog responses never include personal path totals. No schema migration is required.
