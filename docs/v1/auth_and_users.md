# Auth And Users

## Purpose

Allow people to access the product with a stable username/password session model and give admins a basic user-management surface.

## Functional Design

### User outcome

Users can:

- log in with username and password
- stay authenticated across page loads
- log out
- view their current identity and role

Admins can:

- create users
- list users
- reset passwords
- disable or enable users
- delete users, except themselves

### In scope for v1

- bootstrap first admin when no users exist
- server-side session storage using `X-Session-Token`
- role model: `admin` and `user`
- admin-only user lifecycle actions

### Out of scope for v1

- invite codes
- OAuth or SSO
- email-based auth
- role models beyond `admin` and `user`

### Canonical flows

1. First login bootstraps the admin.
2. Existing user logs in and receives a session.
3. Authenticated request resolves current user from session.
4. Admin creates and manages additional users.
5. Logout revokes the user’s sessions.

### Error behavior

- missing credentials: `400`
- invalid credentials: `401`
- missing/invalid session: `401`
- non-admin on admin route: `403`
- duplicate user: `409`
- self-delete or self-disable: `400`

## Technical Design

### Backend contract

- Routes under `/auth`
- Primary endpoints:
  - `POST /auth/login`
  - `GET /auth/me`
  - `POST /auth/logout`
  - `GET /auth/role`
  - `POST /auth/users`
  - `GET /auth/users`
  - `POST /auth/users/reset`
  - `POST /auth/users/disable`
  - `DELETE /auth/users/{username}`

### Frontend contract

- Login route: `/login`
- Admin route: `/admin/users`
- All non-login routes depend on a valid session

### Data model

- `users`
- `sessions`

### Release constraints

- Username handling must be normalized consistently across login, session creation, and user-management flows.
- Session invalidation behavior must be deterministic.
- Auth docs must match actual role and permission rules.
