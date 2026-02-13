# Architecture

## Overview
This project uses a simple three‑tier layout:

- UI (NiceGUI).
- FastAPI backend for auth, course management, learning paths, and tracking.
- Postgres for persistence (schema managed via Alembic).

## Architecture Docs

- Backend details: `docs/architecture_backend.md`
- Frontend details (NiceGUI target): `docs/architecture_frontend.md`
