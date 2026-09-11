# Technical Design: Auth And Sessions

## Goal

Document the current auth/session architecture that supports the v1 release.

## Canonical Backend Flow

1. `POST /auth/login` validates username/password.
2. Auth service loads the user and verifies the bcrypt hash.
3. Auth service creates a server-side session row.
4. Frontend stores the returned token and sends it as `X-Session-Token`.
5. Protected routes resolve the current user from the session token.

## Canonical Frontend Flow

1. User loads `/login`.
2. `SessionStore` performs login via the backend.
3. NiceGUI routes call `require_user(store, api)` before rendering protected content.
4. Admin pages additionally rely on backend role checks.

## Current Implementation Boundaries

- API transport: `backend/api/auth.py`
- service logic: `backend/services/auth_service.py`
- persistence: `backend/database/async_repositories/auth.py`
- session dependency: `backend/api/deps.py`
- UI session management: `frontend/ui/nicegui/core/session_store.py`

## Permissions

- public:
  - `POST /auth/login`
- authenticated:
  - `GET /auth/me`
  - `POST /auth/logout`
  - `GET /auth/role`
- admin only:
  - user-management routes under `/auth/users`

## Data Model

- `users`
  - username
  - password hash
  - role
  - disabled
  - timestamps
- `sessions`
  - token hash
  - colleague/user identifier
  - created/last seen/expires timestamps

## Accepted V1 Constraints

- auth model remains username/password only
- session model remains server-side token based
- only `admin` and `user` roles are supported

## Release Risks

- username normalization must be consistent end-to-end
- user lookup and session creation must use the same canonical identifier
- auth docs and tests must reflect the real permission rules

## Out Of Scope

- OAuth / SSO
- email flows
- invites
- richer role hierarchy
