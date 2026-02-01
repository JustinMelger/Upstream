# Architecture

## Overview
This project uses a simple three‑tier layout:

- Streamlit UI for the colleague‑facing web experience.
- FastAPI backend for auth, course management, learning paths, and tracking.
- SQLite for persistence (seeded from `courses.csv` on startup).

## Mermaid diagram

```mermaid
flowchart LR
  Users[Colleagues + Curators] --> UI[Streamlit UI]

  subgraph API[FastAPI Backend]
    Auth[Auth Service]
    Courses[Course Service]
    Paths[Path Service]
    Tracking[Tracking Service]
  end

  UI --> Auth
  UI --> Courses
  UI --> Paths
  UI --> Tracking

  DB[(SQLite)]
  Auth --> DB
  Courses --> DB
  Paths --> DB
  Tracking --> DB
```

## Service responsibilities (brief)

### Auth service
- Email allow‑list role detection (admin vs user).
- Role enforcement for admin‑only endpoints.

### Course service
- CRUD for courses (title, provider, category, level, duration, url).
- Search and filtering support.

### Path service
- CRUD for learning paths.
- Attach courses to paths (no ordering yet).

### Tracking service
- Track per‑colleague progress (interested / in_progress / completed).
- Aggregate stats (team vs individual).
