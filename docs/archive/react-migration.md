# React migration and compatibility decisions

Historical summary. Current guidance: [architecture](../architecture.md) and [operations](../operations.md).

## 2026-09-09 — React migration validation

The React replacement record reported local verification on 2026-09-09 and was catalogued on 2026-09-11. React/TypeScript, Vite, TanStack Query, Radix and Nginx replaced the NiceGUI runtime. FastAPI/PostgreSQL remained the source of truth. Browser credentials moved to HttpOnly cookies with CSRF and Origin checks; explicit header credentials kept precedence for compatibility.

Teams and AI routes were retired. Old Teams and profile-statistics links received redirects. Team data and historical Alembic migrations were deliberately retained, with destructive cleanup deferred until the rollback window closes and a recoverable backup exists. That retirement has not been authorized by this documentation cleanup.

The original report recorded 164 backend tests, 12 frontend tests, 10 browser workflows and 14 Linux visual comparisons, plus fresh/populated migration checks preserving original fields across 14 tables. These figures are historical evidence, not present-day test counts or deployment status.

## 2026-09-11 — V1 implementation cleanup

The cleanup record reported removal of external-image fetching and unused dependencies while preserving explicit metadata fetching and wire compatibility. It recorded 196 backend tests, 39 frontend tests, 33 browser workflows and 66 visual comparisons, plus a disposable installation and populated migration check. Production deployment was outside that work.

Pre-React architecture proposals emphasized thin routers, service-owned domain rules, repository-owned SQL and bounded projections. Those boundaries survive in the current engineering standards. NiceGUI package layouts and proposed Teams/inbox/AI capabilities do not define the current product.

## Continuing implication

Image rollback and schema retirement are separate decisions. Preserve compatible previous images, authentication transport and retained data until an explicit retirement decision; do not interpret elapsed time or this archive consolidation as permission to delete data.
