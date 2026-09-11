# V1 Status

This page captures the current release posture for v1. It is intentionally narrower than the roadmap and architecture notes.

## Current Rating

- V1 readiness: about 7.8 / 10
- Architecture: about 8 / 10
- Test confidence: about 7.5 / 10

## In V1

- Authenticated sessions and basic user management.
- Admin user management at `/admin/users`.
- Home dashboard at `/home`.
- Explore hub at `/explore`.
- Detail routes for courses, videos, articles, and paths under `/explore/*`.
- Canonical learning-item sharing at `/share/item?type=course|article|video`.
- Canonical path sharing at `/share/path`.
- Mixed learning-item paths.
- Reviews for learning items and paths.
- Course tracking and selected path progress.
- Teams and team activity views.
- Profile and stats at `/profile` and `/profile/stats`.

## Off Or Gated For V1

- AI Curator is gated by `FEATURE_AI_CURATOR=0` by default.
- Product telemetry is gated by `FEATURE_TELEMETRY=0` by default.
- OpenTelemetry tracing/metrics are gated by `OTEL_ENABLED=0` by default.
- The standalone observability stack remains available separately through `docker-compose.observability.yml`.

## Recent Readiness Improvements

- Catalog implementation code moved from `pages/{courses,paths,articles}` to `domains/{courses,paths,articles}`.
- Legacy standalone catalog routes are removed; reusable domain logic remains available to Explore and Share.
- Import boundaries are enforced with Import Linter and CI runs `uv run lint-imports`.
- Home dashboard rendering now uses reusable dashboard primitives.
- Telemetry and tracing are opt-in for v1.

## Post-V1

- Extract activity into a clearer feature/domain boundary.
- Continue frontend simplification where route/detail modules remain dense.
- Add broader e2e coverage after the v1 flow stabilizes.
- Clean historical roadmap/audit notes so current-state docs stay easier to scan.

## Recommended Release Smoke Paths

- Log in -> `/home`.
- Browse `/explore` -> open one course/video/article/path detail.
- Share a learning item through `/share/item`.
- Share a mixed path through `/share/path`.
- Review a learning item or path.
- Admin user management as an admin.
