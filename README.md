# Learning Hub

A simple internal learning hub where colleagues can browse curated courses, track progress, and follow ordered learning paths.

## Docs
- Architecture: [architecture.md](architecture.md)
- Roadmap: [roadmap.md](roadmap.md)

## Run locally (Docker)
### Quick start
1. Build and start services:
   - `docker compose up --build`
2. Open the UI:
   - `http://localhost:8502`

### Environment variables
- `ADMIN_EMAILS`: comma-separated admin emails (API + UI).
- `INVITE_CODE`: optional invite code for login (UI).
- `DATABASE_PATH`: SQLite file path (API).
- `COURSES_CSV`: seed CSV path (API).

## Run locally (without Docker)
1. Install dependencies:
   - `uv sync`
2. Start the API:
   - `uvicorn backend.main:app --reload`
3. Start the UI (in a new terminal):
   - `streamlit run frontend/Home.py`
4. Open the UI:
   - `http://localhost:8501`

## Pages
- Home (Dashboard): progress snapshot, path progress, recent activity, featured paths, and recently added courses.
- Courses: browse + add/remove to My Courses (admins can edit/delete).
- My Courses: update status and remove tracked courses.
- Paths: browse and add to My Paths (admins can edit/delete and set order).
- My Paths: manage selected paths and update course status.

## Login (simple, no OAuth)
- Users sign in on the Login page and stay logged in for the Streamlit session.
- Optional invite code: set `INVITE_CODE` in the UI environment.

## API endpoints (read-first)
- `GET /health`
- `GET /courses`
- `GET /courses/{id}`
- `GET /paths`
- `GET /paths/{id}`
- `GET /tracking?colleague_id=...`
- `POST /tracking`
- `POST /tracking/delete`
- `GET /tracking/stats?colleague_id=...`
- `POST /paths/{id}/select`
- `POST /paths/{id}/unselect`

Admin-only:
- `POST /courses`
- `PUT /courses/{id}`
- `DELETE /courses/{id}`
- `POST /paths`
- `PUT /paths/{id}`
- `DELETE /paths/{id}`
- `GET /tracking/stats` (team stats)
- `GET /tracking/stats/users` (team stats by user)

## Roles (temporary, email-based)
- Admins can add/edit/delete courses and manage paths.
- Users can browse courses, manage My Courses, and manage My Paths.
- Admins are defined by `ADMIN_EMAILS` in `docker-compose.yml` (comma‑separated).

## Tracking
- Set status per course: `interested`, `in_progress`, or `completed` (My Courses or My Paths).
- Remove a tracked course from My Courses if needed.

## Paths
- Create learning paths by selecting courses and ordering them (admin only).
- Add a path to My Paths from the Paths page.
- Update per-course status inside My Paths.
- Delete paths (admin only).

## Data
- Courses are seeded from `courses.csv` into SQLite on startup.
- Database file: `learning_hub.db` (not intended for Git).
