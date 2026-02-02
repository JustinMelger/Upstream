# Roadmap

## Phase 1 — MVP catalog
- Stable data model for courses (CSV-based).
- Search + filter UI.
- One-click course links.
- Basic “Add course” form for curators.

## Phase 2 — Management + paths
- Edit/delete courses.
- Learning paths with ordered sequences.
- Path overview page with progress per path.

## Phase 3 — Auth v1 (self-hosted + optional OAuth)
- Add `/auth/login`, `/auth/callback`, `/auth/me`, `/auth/logout` API routes.
- Session storage (signed cookies or server-side store).
- Invite-code login (email + code) as the default flow.
- Optional OAuth configuration (Google/Microsoft/Okta) via env vars.
- UI: login screen + guard all pages.
- Admin allowlist (`ADMIN_EMAILS`) applied post-auth.

## Phase 4 — UI migration to NiceGUI
- Create NiceGUI shell app with shared navigation and layout.
- Port login/session flow to NiceGUI (reuse backend auth).
- Port core pages: Home/Dashboard, Courses, My Courses.
- Port Paths + My Paths (including ordering UI and admin edit flows).
- Parity check + remove Streamlit UI once stable.

## Phase 5 — Colleague tracking + analytics
- Colleague profiles with interest/completion tracking.
- Basic analytics (popular courses, completion rates).

## Phase 6 — Data durability + polish
- Import/export tools for course data.
- UI polish + accessibility improvements.
