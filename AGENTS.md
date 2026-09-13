# Engineering standards

Upstream uses a React/TypeScript frontend and FastAPI/PostgreSQL backend. `docs/README.md` indexes current product, architecture, and operations guidance. The decision archive provides context, not current implementation instructions.

## Backend

Keep API routers thin, business rules in services, and SQL in `backend/database/async_repositories`. Repositories must not import services or API modules. Use request-owned transactions, explicit domain errors, typed public schemas, and migrations for schema changes. Do not edit historical migrations. Preserve current-user/owner/admin authorization independently of frontend checks. Read runtime settings through `backend/core/config.py`.

## Frontend

The supported UI is `frontend/react`. Use React, TypeScript, Vite, React Router, TanStack Query, Radix primitives, CSS Modules, and shared tokens. Keep API requests in `src/lib/api` or feature query hooks. Generate public types from OpenAPI. Server state belongs in the query cache, shareable filters in URLs, and ephemeral form state locally. Never store session credentials in JavaScript storage. Maintain keyboard/focus behavior and visible error/loading/empty states. Keep pages focused: Explore for discovery, My learning for next actions, Activity for stats and shared updates.

## Scope

Teams/memberships and AI Curator are retired. Articles/videos support reviews and owner/admin edits/deletion, but not completion tracking. Course-only path progress is independent of manual path status. Keep shared content global and personal progress private. Avoid invented historical analytics and duplicate dashboards.

## Validation

Use a dedicated disposable database for backend tests: fixtures truncate tables. Run relevant backend tests, Ruff, mypy, import contracts, frontend type/lint/unit/build checks, and browser workflows for UI changes. Update the OpenAPI JSON and generated TypeScript contracts with API changes. Browser seed data is only permitted in explicitly disposable databases. Never delete retained team data during the rollback window.

Keep public module/function docstrings clear and concise. Prefer composition and explicit dependencies, focused modules, simple local state, and behavior-based tests. Do not add abstractions without concrete reuse. Update current docs when product behavior, deployment, or commands change.
