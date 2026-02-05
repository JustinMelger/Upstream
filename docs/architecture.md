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

## Auth Architecture

### Auth Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as Streamlit UI
  participant API as Auth Router (FastAPI)
  participant Auth as Auth Service
  participant DB as SQLite Database

  User->>UI: Submit username + password
  UI->>API: POST /auth/login
  API->>Auth: authenticate_user(username, password)
  Auth->>DB: SELECT user by username
  DB-->>Auth: user row
  Auth-->>API: user metadata or None

  alt Valid credentials
    API->>Auth: create_session(username)
    Auth->>DB: INSERT session(token_hash, expires_at)
    DB-->>Auth: ok
    API-->>UI: {token, expires_at, role}
  else Invalid credentials
    API-->>UI: 401 invalid_credentials
  end
```

### Auth Domain Overview

```mermaid
classDiagram
  class AuthRouter {
    +POST /auth/login
    +GET /auth/me
    +POST /auth/logout
    +GET /auth/role
    +POST /auth/users
    +GET /auth/users
    +POST /auth/users/reset
    +DELETE /auth/users/:username
    +POST /auth/users/disable
  }

  class AuthService {
    +authenticate_user(username, password): dict|None
    +create_session(username): dict
    +get_session(token): dict|None
    +revoke_sessions(username): int
    +create_user(username, password, role): dict
    +update_password(username, password): int
    +delete_user(username): int
    +set_user_disabled(username, disabled): int
    +list_users(): list[dict]
    +is_admin(username): bool
  }

  class AuthRepository {
    +get_user(username): dict|None
    +has_users(): bool
    +create_user(username, password_hash, role, now): None
    +list_users(): list[dict]
    +update_password(username, password_hash, now): int
    +delete_user(username): int
    +set_user_disabled(username, disabled, now): int
    +create_session(colleague_id, token_hash, created_at, last_seen, expires_at): None
    +get_session(token_hash): dict|None
    +update_session_last_seen(token_hash, last_seen): None
    +delete_session(token_hash): int
    +revoke_sessions(colleague_id): int
    +purge_expired_sessions(now): int
    +update_last_login(username, now): None
  }

  class SQLiteAuthRepository {
  }

  class SQLiteDatabase {
    +SQLiteDatabase(db_path: str)
    +get_conn(): Connection
    +init_db(): None
    +seed_courses_from_csv(csv_path: Path): None
  }

  AuthRouter --> AuthService : request handling
  AuthService --> AuthRepository : persistence
  SQLiteAuthRepository ..|> AuthRepository
  SQLiteAuthRepository --> SQLiteDatabase : uses connections
```

### Auth Data Model

```mermaid
erDiagram
  USERS ||--o{ SESSIONS : "has active sessions"
  USERS {
    INTEGER id
    STRING username
    STRING password_hash
    STRING role
    TIMESTAMP created_at
    TIMESTAMP updated_at
    TIMESTAMP last_login_at
    INTEGER disabled
  }
  SESSIONS {
    INTEGER id
    STRING colleague_id
    STRING token_hash
    TIMESTAMP created_at
    TIMESTAMP last_seen
    TIMESTAMP expires_at
  }
```

## Service responsibilities (brief)

### Auth service
- Bootstrap admin creation when no users exist.
- Username/password authentication with bcrypt.
- Session creation, validation, and revocation.
- Admin-only user management (create, reset, disable, delete, list).

### Course service
- CRUD for courses (title, provider, category, level, duration, url).
- Search and filter by query/provider/category/level.
- Admin-only create/update/delete.

### Path service
- CRUD for learning paths with ordered course lists.
- User path selection, unselection, and status updates.
- Admin-only create/update/delete for paths.

### Tracking service
- Track per-user course progress (interested / in_progress / completed).
- Recent activity and stats (per-user and team).
- Admin-only team-wide stats.

## Courses Architecture

### Courses Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as Streamlit UI
  participant API as Courses Router (FastAPI)
  participant Auth as Auth Service
  participant Courses as Courses Service
  participant DB as SQLite Database

  User->>UI: Request courses list
  UI->>API: GET /courses
  API->>Auth: get_session(token)
  Auth->>DB: SELECT session by token_hash
  DB-->>Auth: session row
  Auth-->>API: username or unauthorized
  API->>Courses: list_courses(filters)
  Courses->>DB: SELECT courses with filters
  DB-->>Courses: rows
  API-->>UI: list[course]
```

### Courses Domain Overview

```mermaid
classDiagram
  class CoursesRouter {
    +GET /courses
    +GET /courses/:course_id
    +POST /courses
    +PUT /courses/:course_id
    +DELETE /courses/:course_id
  }

  class CoursesService {
    +list_courses(query, provider, category, level): list[dict]
    +get_course_by_id(course_id): dict|None
    +create_course(payload): dict
    +update_course(course_id, payload): dict|None
    +delete_course(course_id): bool
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  class SQLiteDatabase {
    +get_conn(): Connection
  }

  CoursesRouter --> AuthService : require_session + admin checks
  CoursesRouter --> CoursesService : CRUD
  CoursesService --> SQLiteDatabase : persistence
```

### Courses Data Model

```mermaid
erDiagram
  COURSES {
    INTEGER id
    STRING title
    STRING provider
    STRING category
    STRING level
    NUMERIC duration_hours
    STRING url
    TIMESTAMP created_at
  }
```

## Paths Architecture

### Paths Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as Streamlit UI
  participant API as Paths Router (FastAPI)
  participant Auth as Auth Service
  participant Paths as Paths Service
  participant UserPaths as User Paths Service
  participant DB as SQLite Database

  User->>UI: Create learning path
  UI->>API: POST /paths
  API->>Auth: require_session + is_admin
  Auth->>DB: SELECT session + user role
  DB-->>Auth: session + role
  Auth-->>API: authorized
  API->>Paths: create_path(payload)
  Paths->>DB: INSERT paths + path_courses
  DB-->>Paths: ok
  API-->>UI: path payload

  User->>UI: Select path
  UI->>API: POST /paths/{path_id}/select
  API->>UserPaths: add_user_path(user, path_id)
  UserPaths->>DB: INSERT user_paths
  DB-->>UserPaths: ok
  API-->>UI: selection payload
```

### Paths Domain Overview

```mermaid
classDiagram
  class PathsRouter {
    +GET /paths
    +GET /paths/:path_id
    +POST /paths
    +PUT /paths/:path_id
    +DELETE /paths/:path_id
    +POST /paths/:path_id/select
    +POST /paths/:path_id/unselect
    +POST /paths/:path_id/status
    +GET /paths/selected/list
  }

  class PathsService {
    +list_paths(): list[dict]
    +get_path(path_id): dict|None
    +create_path(payload): dict
    +update_path(path_id, payload): dict
    +delete_path(path_id): bool
  }

  class UserPathsService {
    +add_user_path(user, path_id): dict
    +remove_user_path(user, path_id): int
    +update_user_path_status(user, path_id, status): int
    +list_user_paths(user): list[dict]
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  class SQLiteDatabase {
    +get_conn(): Connection
  }

  PathsRouter --> AuthService : require_session + admin checks
  PathsRouter --> PathsService : CRUD
  PathsRouter --> UserPathsService : selection + status
  PathsService --> SQLiteDatabase : persistence
  UserPathsService --> SQLiteDatabase : persistence
```

### Paths Data Model

```mermaid
erDiagram
  PATHS ||--o{ PATH_COURSES : "includes"
  PATHS {
    INTEGER id
    STRING name
    STRING description
  }
  PATH_COURSES {
    INTEGER id
    INTEGER path_id
    INTEGER course_id
    INTEGER position
  }
  USER_PATHS {
    INTEGER id
    STRING colleague_id
    INTEGER path_id
    TIMESTAMP created_at
    TIMESTAMP updated_at
    STRING status
  }
```

## Tracking Architecture

### Tracking Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as Streamlit UI
  participant API as Tracking Router (FastAPI)
  participant Auth as Auth Service
  participant Tracking as Tracking Service
  participant DB as SQLite Database

  User->>UI: Update tracking status
  UI->>API: POST /tracking
  API->>Auth: require_session
  Auth->>DB: SELECT session
  DB-->>Auth: session row
  Auth-->>API: username
  API->>Tracking: upsert_tracking(user, course_id, status)
  Tracking->>DB: INSERT/UPDATE tracking
  DB-->>Tracking: ok
  API-->>UI: tracking payload

  User->>UI: View team stats (admin)
  UI->>API: GET /tracking/stats
  API->>Auth: require_session + is_admin
  Auth-->>API: authorized
  API->>Tracking: stats_all()
  Tracking->>DB: SELECT counts by status
  DB-->>Tracking: rows
  API-->>UI: stats payload
```

### Tracking Domain Overview

```mermaid
classDiagram
  class TrackingRouter {
    +GET /tracking
    +POST /tracking
    +POST /tracking/delete
    +GET /tracking/stats
    +GET /tracking/stats/users
    +GET /tracking/recent
  }

  class TrackingService {
    +list_tracking(colleague_id): list[dict]
    +upsert_tracking(colleague_id, course_id, status): dict
    +remove_tracking(colleague_id, course_id): int
    +stats_for_colleague(colleague_id): dict
    +stats_all(): dict
    +stats_by_user(): list[dict]
    +list_recent_activity(limit): list[dict]
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  class SQLiteDatabase {
    +get_conn(): Connection
  }

  TrackingRouter --> AuthService : require_session + admin checks
  TrackingRouter --> TrackingService : query + mutate
  TrackingService --> SQLiteDatabase : persistence
```

### Tracking Data Model

```mermaid
erDiagram
  TRACKING {
    INTEGER id
    STRING colleague_id
    INTEGER course_id
    STRING status
    TIMESTAMP updated_at
  }
```
