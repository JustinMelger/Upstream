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

## Auth design (self-hosted)

```mermaid
sequenceDiagram
  participant U as User
  participant UI as Streamlit UI
  participant API as FastAPI Auth Router
  participant S as Session Store
  participant OP as OAuth Provider (optional)

  U->>UI: Open app
  UI->>API: GET /auth/me
  API->>S: Check session
  S-->>API: Session found / not found
  API-->>UI: 200 user / 401

  alt Invite code mode
    U->>UI: Submit email + invite code
    UI->>API: POST /auth/login
    API->>S: Create session
    API-->>UI: Set session cookie
  else OAuth mode
    U->>UI: Click Sign in
    UI->>API: GET /auth/login
    API-->>UI: Redirect to OP
    U->>OP: Approve consent
    OP-->>API: Redirect /auth/callback?code=...
    API->>OP: Exchange code for token
    API-->>API: Fetch userinfo
    API->>S: Create session
    API-->>UI: Set session cookie
  end
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
- Attach courses to paths with explicit ordering.

### Tracking service
- Track per‑colleague progress (interested / in_progress / completed).
- Aggregate stats (team vs individual).
