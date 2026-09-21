# Administrator role management — implementation record

Implemented 2026-09-21. Current behavior is documented in [product guidance](../product.md).

The existing Manage menu now offers role promotion/demotion with confirmation, local pending/error feedback, list refresh, and focus restoration. `PATCH /auth/users/{username}/role` accepts `admin` or `user` and returns the canonical username and role. No migration or session revocation accompanies a role change; navigation refreshes on reload.

Role changes, disabling/enabling, and deletion share transaction-scoped PostgreSQL advisory lock `(852741, 1)`. The account-management authentication dependency acquires it before session last-seen writes, avoiding lock-order deadlocks when another operation revokes that session. Services also acquire the lock and reread actor and target before mutation. Authorization, self-protection, and the enabled-administrator count are enforced server-side. Disabled administrators do not count toward recovery access.

Focused regression coverage includes live-session permissions, validation, browser CSRF, disabled accounts, self-protection, competing administrator operations, and browser confirmation/retry/focus behavior. No production deployment is included.

Verification on 2026-09-21:

- Full backend suite: 207 passed against an isolated PostgreSQL 17 container. After adding four defensive-count cases, the focused role suite passed all 12 tests.
- Frontend unit suite: 46 passed; supporting-page browser suite: 7 passed, including role confirmation, retry, disabled submissions and focus restoration.
- Existing Admin page/create-dialog baselines matched at 390px, 768px and 1440px. Six new promotion/demotion baselines were generated and visually reviewed at those same widths.
- Ruff, mypy, import boundaries, frontend formatting/lint/typing, generated OpenAPI check and production build passed. Vite emitted its existing PostCSS `from` warning; compilation succeeded.
