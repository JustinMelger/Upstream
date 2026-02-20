# Architecture

## Overview
This project uses a simple three‑tier layout:

- UI (NiceGUI, using a lightweight MVC pattern in frontend pages).
- FastAPI backend for auth, course management, learning paths, and tracking.
- Articles sharing (links) for colleagues.
- Postgres for persistence (schema managed via Alembic).

## Architecture Docs

- Backend details: `docs/architecture_backend.md`
- Frontend details (NiceGUI): `docs/architecture_frontend.md`
