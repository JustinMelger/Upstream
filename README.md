# Learning Hub

A simple internal website where colleagues can browse a curated list of courses, track progress, and jump to the provider.

## Docs
- Architecture: [architecture.md](architecture.md)
- Roadmap: [requirements.md](requirements.md)

## Run locally (Docker)
1. Build and start services:
   - `docker compose up --build`
2. Open the UI:
   - `http://localhost:8502`

## Run locally (without Docker)
1. Install dependencies:
   - `uv sync`
2. Start the API:
   - `uvicorn backend.main:app --reload`
3. Start the UI (in a new terminal):
   - `streamlit run frontend/app.py`
4. Open the UI:
   - `http://localhost:8501`

## API endpoints (read-first)
- `GET /health`
- `GET /courses`
- `GET /courses/{id}`
- `GET /tracking?colleague_id=...`
- `POST /tracking`
- `GET /tracking/stats?colleague_id=...`

Admin-only:
- `POST /courses`
- `PUT /courses/{id}`
- `DELETE /courses/{id}`
- `GET /tracking/stats` (team stats)

## Roles (temporary, email-based)
- Admins can add/edit/delete courses and see team stats.
- Users can browse courses and track their own progress.
- Admins are defined by `ADMIN_EMAILS` in `docker-compose.yml` (comma‑separated).

## Tracking
- Enter your name/email in the sidebar.
- Set status per course: `interested`, `in_progress`, or `completed`.
- Stats show in the sidebar (team stats for admins).

## Data
- Courses are seeded from `courses.csv` into SQLite on startup.
- Database file: `learning_hub.db` (not intended for Git).
