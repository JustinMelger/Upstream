# Backend Architecture

## Overview
The backend is a FastAPI application organized as:

- Routers (HTTP endpoints).
- Dependencies (request-scoped construction + auth guards).
- Services (domain logic).
- Repositories (persistence).
- Postgres (schema managed via Alembic).

The backend also includes an observability layer:
- OpenTelemetry traces + metrics initialization at app startup.
- Authenticated frontend product-event ingestion via `POST /telemetry/events`.
- OTLP export to an OpenTelemetry Collector (fan-out to Tempo/Prometheus).
- Logs shipped by Promtail into Loki for Grafana log exploration.

## High-Level Diagram

```mermaid
flowchart LR
  Users[Colleagues + Curators] --> UI[UI]

  subgraph API[FastAPI Backend]
    Auth[Auth Service]
    Courses[Course Service]
    Paths[Path Service]
    Tracking[Tracking Service]
    Notifications[Notifications Service]
    Telemetry[Telemetry Service]
  end

  UI --> Auth
  UI --> Courses
  UI --> Paths
  UI --> Tracking
  UI --> Notifications
  UI --> Telemetry

  DB[(Postgres)]
  Auth --> DB
  Courses --> DB
  Paths --> DB
  Tracking --> DB
  Notifications --> DB

  OTel[OpenTelemetry SDK]
  Collector[OpenTelemetry Collector]
  Prom[Prometheus]
  Tempo[Grafana Tempo]
  Loki[Grafana Loki]
  Promtail[Promtail]
  DockerLogs[Docker container logs]
  Grafana[Grafana UI]
  API --> OTel
  OTel --> Collector
  Collector --> Prom
  Collector --> Tempo
  DockerLogs --> Promtail
  Promtail --> Loki
  Prom --> Grafana
  Tempo --> Grafana
  Loki --> Grafana
```

## Observability Architecture

### Runtime wiring
- `backend/main.py` initializes observability with `configure_observability(app)` when `OTEL_ENABLED=1`.
- `backend/core/observability.py` configures:
  - Tracer provider + OTLP trace exporter.
  - Meter provider + OTLP metrics exporter.
  - FastAPI / HTTPX / SQLAlchemy instrumentation.

### Telemetry ingestion flow
- Frontend emits product events to `POST /telemetry/events` (authenticated).
- Router: `backend/api/telemetry.py`
- Service: `backend/services/telemetry_service.py`
- Current behavior:
  - Increments metric counter `frontend_events_total`.
  - Emits span `frontend.event` with event attributes.
  - Logs a structured fallback line for operational debugging.

### Key environment settings
- `OTEL_ENABLED`
- `OTEL_SERVICE_NAME`
- `OTEL_SERVICE_VERSION`
- `OTEL_DEPLOYMENT_ENVIRONMENT`
- `OTEL_TRACES_SAMPLE_RATIO`
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
- `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`
- `OTEL_EXPORTER_OTLP_HEADERS`

### Local Grafana stack wiring
- Observability stack runs separately via `docker-compose.observability.yml`.
- Collector exports traces to Tempo (`TEMPO_OTLP_ENDPOINT`, default `http://tempo:4318/v1/traces`).
- Collector exports metrics in Prometheus format on `:9464`; Prometheus scrapes Collector.
- Promtail discovers Docker containers and ships logs to Loki.
- Grafana is configured with provisioned datasources for:
  - Prometheus (`http://prometheus:9090`)
  - Tempo (`http://tempo:3200`)
  - Loki (`http://loki:3100`)

## Auth Architecture

### Auth Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as NiceGUI UI
  participant API as Auth Router (FastAPI)
  participant Auth as Auth Service
  participant DB as Postgres Database

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

  class SQLAuthRepository {
  }

  AuthRouter --> AuthService : request handling
  AuthService --> AuthRepository : persistence
  SQLAuthRepository ..|> AuthRepository
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

## Service Responsibilities (Brief)

### Auth service
- Bootstrap admin creation when no users exist.
- Username/password authentication with bcrypt.
- Session creation, validation, and revocation.
- Admin-only user management (create, reset, disable, delete, list).

### Course service
- CRUD for courses (`title`, `description`, `learning_outcomes`, `prerequisites`, `language`, `provider`, `category`, `level`, `duration_hours`, `url`).
- Search and filter by query/provider/category/level.
- Any authenticated user can create courses; only the creator (or admin) can edit/delete.
- Validates create/update payloads at the service boundary via typed `_parse_mutation_payload`.
- Enriches course payloads with computed `search_document` content and best-effort URL preview image URLs.
- Enforces duplicate protection on create (`url`, normalized title+provider).

### Path service
- CRUD for learning paths with ordered course lists.
- User path selection, unselection, and status updates.
- Any authenticated user can create paths; only the creator (or admin) can edit/delete.

### Tracking service
- Track per-user course progress (interested / in_progress / completed).
- Recent activity and stats with explicit auth rules:
  - `GET /tracking?colleague_id=X`: self always allowed, other users require admin.
  - `GET /tracking/stats?colleague_id=X`: self always allowed, other users require admin.
  - `GET /tracking/stats` without `colleague_id`: team totals, admin only.
  - `GET /tracking/stats/users` and `GET /tracking/recent`: admin only.

### Articles service
- Allow colleagues to share links (title, URL, optional tags).
- Browse/search colleague-submitted links.
- Authenticated users can create articles and review article links.

### Videos service
- Allow colleagues to share video links as first-class learning items (`title`, `description`, `provider`, `category`, `url`).
- Browse/search colleague-submitted videos with preview metadata enrichment.
- Authenticated users can create videos; the current phase keeps videos lightweight and does not add tracking/recommendation/review write models.

### Notifications service
- Aggregates share/recommend/review events into activity feed payloads.
- Supports mailbox-style scopes: `inbox` (personal) and `team` (team-wide timeline).

### Telemetry service
- Accepts low-risk frontend product telemetry events (`event_name`, optional context, timestamp).
- Records event count + tracing attributes for product-loop analysis and operability.
- Keeps ingestion auth-protected via `require_session`.

## API Error Handling

Service-layer failures are represented by domain-specific `ServiceError` exceptions (for example `AuthServiceError`, `CoursesServiceError`, `PathsServiceError`, `UserPathsServiceError`, `TrackingServiceError`). The FastAPI app registers exception handlers that convert these into a standard JSON payload:

```json
{
  "status": "error",
  "message": "missing_title",
  "timestamp": "2026-02-07T12:34:56.789012+00:00"
}
```

Endpoints still use `HTTPException` directly for request/permission semantics (for example `401 unauthorized`, `403 admin_required`, `404 not_found`).

## Request Validation

Each router defines Pydantic request and response schemas. Invalid request payloads (wrong types, missing required fields, invalid list element types) are rejected with `422 Unprocessable Entity` before service methods run.

## Service Input Boundary

Services must parse externally influenced inputs at the service boundary using typed Pydantic dataclass `_parse_*` helpers.

Required contract:
- Each service entrypoint that accepts request/user-provided values calls a local `_parse_*` helper before business logic.
- Each `_parse_*` helper catches `ValidationError` and raises the domain `*ServiceError` with:
  - `detail="invalid_payload"`
  - `status_code=400`

This keeps router-level schema validation and service-level domain validation aligned, and provides deterministic error semantics for tests and clients.

### Service Payload Boundary Matrix

This matrix is the enforceable contract for service-boundary input parsing.

| Service file | Entrypoints covered | Parse helpers | Guard test |
| --- | --- | --- | --- |
| `backend/services/auth_service.py` | `is_admin`, `create_session`, `get_session`, `revoke_sessions`, `get_user`, `create_user`, `update_password`, `delete_user`, `authenticate_user`, `set_user_disabled` | `_parse_username_payload`, `_parse_session_payload`, `_parse_create_user_payload`, `_parse_update_password_payload`, `_parse_set_disabled_payload`, `_parse_authenticate_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/courses_service.py` | `create_course`, `update_course` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/paths_service.py` | `create_path`, `update_path` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/articles_service.py` | `create_article` | `_parse_create_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/videos_service.py` | `create_video` | `_parse_create_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/course_reviews_service.py` | `create_review` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/path_reviews_service.py` | `create_review` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/article_reviews_service.py` | `create_review` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/course_recommendations_service.py` | `create_recommendation` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/path_recommendations_service.py` | `create_recommendation` | `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/tracking_service.py` | `list_tracking`, `list_recent_activity`, `upsert_tracking`, `remove_tracking` | `_parse_list_payload`, `_parse_recent_activity_payload`, `_parse_mutation_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/user_paths_service.py` | `add_user_path`, `list_user_paths`, `remove_user_path`, `update_user_path_status` | `_parse_mutation_payload`, `_parse_list_payload` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |
| `backend/services/notifications_service.py` | `list_activity` | `_parse_activity_query` | `tests/backend/test_architecture_service_payload_contracts.py::test_service_entrypoints_use_typed_parse_helpers` + `tests/backend/test_architecture_service_payload_contracts.py::test_parse_helpers_map_validation_error_to_invalid_payload_domain_error` |

## Courses Architecture

### Courses Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as NiceGUI UI
  participant API as Courses Router (FastAPI)
  participant Auth as Auth Service
  participant Courses as Courses Service
  participant DB as Postgres Database

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
    +GET /courses/reviews/summary
    +GET /courses/recommendations/summary
    +GET /courses/:course_id
    +POST /courses
    +PUT /courses/:course_id
    +DELETE /courses/:course_id
    +GET /courses/:course_id/reviews
    +POST /courses/:course_id/reviews
    +DELETE /courses/:course_id/reviews/:review_id
    +GET /courses/:course_id/recommendations
    +POST /courses/:course_id/recommendations
    +DELETE /courses/:course_id/recommendations/:recommendation_id
  }

  class CoursesService {
    +list_courses(query, provider, category, level): list[dict]
    +get_course_by_id(course_id): dict|None
    +create_course(payload): dict
    +update_course(course_id, payload): dict|None
    +delete_course(course_id): bool
  }

  class CoursesRepository {
    +list_courses(query, provider, category, level): list[CourseRecord]
    +get_course_by_id(course_id): CourseRecord|None
    +create_course(payload: CreateCoursePayload): int
    +find_course_by_url(url): CourseRecord|None
    +find_course_by_title_provider(title, provider): CourseRecord|None
    +update_course(payload: UpdateCoursePayload): int
    +delete_course(course_id): int
  }

  class CourseReviewsService {
    +list_reviews(course_id): list[dict]
    +create_review(course_id, payload, created_by): dict (upsert per user)
    +get_review_by_id(review_id): dict|None
    +delete_review(review_id): bool
    +summaries(course_ids): list[dict]
  }

  class CourseRecommendationsService {
    +list_recommendations(course_id): list[dict]
    +create_recommendation(course_id, payload, created_by): dict (upsert per user)
    +get_recommendation_by_id(recommendation_id): dict|None
    +delete_recommendation(recommendation_id): bool
    +summaries(course_ids): list[dict]
  }

  class SQLCoursesRepository {
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  CoursesRouter --> AuthService : require_session + admin checks
  CoursesRouter --> CoursesService : CRUD
  CoursesRouter --> CourseReviewsService : reviews
  CoursesRouter --> CourseRecommendationsService : recommendations
  CoursesService --> CoursesRepository : persistence
  SQLCoursesRepository ..|> CoursesRepository
```

### Courses Data Model

```mermaid
erDiagram
  COURSES {
    INTEGER id
    STRING title
    STRING description
    STRING learning_outcomes
    STRING prerequisites
    STRING language
    STRING provider
    STRING category
    STRING level
    NUMERIC duration_hours
    STRING url
    TIMESTAMP created_at
    STRING created_by
  }
  COURSE_REVIEWS {
    INTEGER id
    INTEGER course_id
    INTEGER rating
    STRING text
    STRING created_by
    TIMESTAMP created_at
  }
  COURSE_RECOMMENDATIONS {
    INTEGER id
    INTEGER course_id
    STRING note
    STRING created_by
    TIMESTAMP created_at
  }
```

`search_document` is computed in `CoursesService` and returned in API payloads; it is not persisted as a physical database column.

Course review/recommendation write model details:
- `POST /courses/{course_id}/reviews` and `POST /courses/{course_id}/recommendations` are idempotent per user/course pair (create-or-update semantics).
- DB uniqueness is enforced on `(course_id, created_by)` in both `course_reviews` and `course_recommendations`.
- Mutation writes update `created_at` as the latest write timestamp (there is no separate `updated_at` column for these tables).

## Paths Architecture

### Paths Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as NiceGUI UI
  participant API as Paths Router (FastAPI)
  participant Auth as Auth Service
  participant Paths as Paths Service
  participant UserPaths as User Paths Service
  participant DB as Postgres Database

  User->>UI: Create learning path
  UI->>API: POST /paths
  API->>Auth: require_session
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
    +GET /paths/reviews/summary
    +GET /paths/recommendations/summary
    +GET /paths/:path_id
    +POST /paths
    +PUT /paths/:path_id
    +DELETE /paths/:path_id
    +POST /paths/:path_id/select
    +POST /paths/:path_id/unselect
    +POST /paths/:path_id/status
    +GET /paths/selected/list
    +GET /paths/:path_id/reviews
    +POST /paths/:path_id/reviews
    +DELETE /paths/:path_id/reviews/:review_id
    +GET /paths/:path_id/recommendations
    +POST /paths/:path_id/recommendations
    +DELETE /paths/:path_id/recommendations/:recommendation_id
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

  class PathReviewsService {
    +list_reviews(path_id): list[dict]
    +create_review(path_id, payload, created_by): dict
    +delete_review(review_id): bool
    +summaries(path_ids): list[dict]
  }

  class PathRecommendationsService {
    +list_recommendations(path_id): list[dict]
    +create_recommendation(path_id, payload, created_by): dict
    +delete_recommendation(recommendation_id): bool
    +summaries(path_ids): list[dict]
  }

  class PathsRepository {
    +list_paths(): list[PathRecord]
    +get_path(path_id): (PathRecord, list[PathCourseRecord])|None
    +create_path_with_courses(name, description, course_ids, created_by): int
    +path_name_exists(name): bool
    +path_name_exists_for_other_id(path_id, name): bool
    +update_path_with_courses(path_id, name, description, course_ids): int
    +delete_path_with_courses(path_id): int
  }

  class SQLPathsRepository {
  }

  class UserPathsRepository {
    +add_user_path(colleague_id, path_id, now): int
    +list_user_paths(colleague_id): list[SelectedPathRecord]
    +remove_user_path(colleague_id, path_id): int
    +update_user_path_status(colleague_id, path_id, status, now): int
  }

  class SQLUserPathsRepository {
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  PathsRouter --> AuthService : require_session + admin checks
  PathsRouter --> PathsService : CRUD
  PathsRouter --> UserPathsService : selection + status
  PathsRouter --> PathReviewsService : reviews
  PathsRouter --> PathRecommendationsService : recommendations
  PathsService --> PathsRepository : persistence
  SQLPathsRepository ..|> PathsRepository
  UserPathsService --> UserPathsRepository : persistence
  SQLUserPathsRepository ..|> UserPathsRepository
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
  PATH_REVIEWS {
    INTEGER id
    INTEGER path_id
    INTEGER rating
    STRING text
    STRING created_by
    TIMESTAMP created_at
  }
  PATH_RECOMMENDATIONS {
    INTEGER id
    INTEGER path_id
    STRING note
    STRING created_by
    TIMESTAMP created_at
  }
```

## Tracking Architecture

### Tracking Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as NiceGUI UI
  participant API as Tracking Router (FastAPI)
  participant Auth as Auth Service
  participant Tracking as Tracking Service
  participant DB as Postgres Database

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

  User->>UI: View tracking stats
  UI->>API: GET /tracking/stats
  API->>Auth: require_session
  alt colleague_id provided
    alt colleague_id == current_user
      API->>Tracking: stats_for_colleague(current_user)
      Tracking->>DB: SELECT counts by status for user
      DB-->>Tracking: rows
      API-->>UI: stats payload
    else colleague_id != current_user
      API->>Auth: is_admin(current_user)
      alt admin
        API->>Tracking: stats_for_colleague(colleague_id)
        Tracking->>DB: SELECT counts by status for user
        DB-->>Tracking: rows
        API-->>UI: stats payload
      else not admin
        API-->>UI: 403 admin_required
      end
    end
  else no colleague_id
    API->>Auth: is_admin(current_user)
    alt admin
      API->>Tracking: stats_all()
      Tracking->>DB: SELECT counts by status for team
      DB-->>Tracking: rows
      API-->>UI: stats payload
    else not admin
      API-->>UI: 403 admin_required
    end
  end
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

  class TrackingRepository {
    +list_tracking(colleague_id): list[TrackingRecord]
    +list_recent_activity(limit): list[TrackingRecord]
    +stats_for_colleague(colleague_id): dict
    +stats_all(): dict
    +stats_by_user(): list[dict]
    +upsert_tracking(colleague_id, course_id, status, updated_at): None
    +remove_tracking(colleague_id, course_id): int
  }

  class SQLTrackingRepository {
  }

  class AuthService {
    +get_session(token): dict|None
    +is_admin(username): bool
  }

  TrackingRouter --> AuthService : require_session + admin checks
  TrackingRouter --> TrackingService : query + mutate
  TrackingService --> TrackingRepository : persistence
  SQLTrackingRepository ..|> TrackingRepository
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

## Articles Architecture

### Articles Endpoints

- `GET /articles`: List/search shared links.
- `POST /articles`: Share a link (authenticated users).
- `GET /articles/reviews/summary`: Review summary rows by article id.
- `GET /articles/{article_id}/reviews`: List article reviews.
- `POST /articles/{article_id}/reviews`: Create/update current user's review.
- `DELETE /articles/{article_id}/reviews/{review_id}`: Delete review (owner/admin).

### Articles Domain Overview

```mermaid
classDiagram
  class ArticlesRouter {
    +GET /articles
    +POST /articles
    +GET /articles/reviews/summary
    +GET /articles/:article_id/reviews
    +POST /articles/:article_id/reviews
    +DELETE /articles/:article_id/reviews/:review_id
  }

  class ArticlesService {
    +list_articles(query, tag): list[dict]
    +create_article(payload, created_by): dict
    +get_article_by_id(article_id): dict|None
  }

  class ArticleReviewsService {
    +list_reviews(article_id): list[dict]
    +create_review(article_id, payload, created_by): dict
    +delete_review(review_id): bool
    +summaries(article_ids): list[dict]
  }

  class ArticlesRepository {
    +list_articles(query, tag): list[ArticleRecord]
    +create_article(title, url, tags, created_by, created_at): int
    +get_article_by_id(article_id): ArticleRecord|None
  }

  class ArticleReviewsRepository {
    +list_for_article(article_id): list[ArticleReviewRecord]
    +create_review(article_id, rating, text, created_by, created_at): int
    +get_review_for_article_by_user(article_id, created_by): ArticleReviewRecord|None
    +update_review(review_id, rating, text, created_at): int
    +delete_review(review_id): int
    +summaries_for_articles(article_ids): dict
  }

  ArticlesRouter --> ArticlesService : links CRUD
  ArticlesRouter --> ArticleReviewsService : reviews
  ArticlesService --> ArticlesRepository : persistence
  ArticleReviewsService --> ArticleReviewsRepository : persistence
```

### Articles Data Model

```mermaid
erDiagram
  USERS ||--o{ ARTICLES : "shares"
  ARTICLES {
    INTEGER id
    STRING title
    STRING url
    STRING tags
    STRING created_by
    TIMESTAMP created_at
  }
  ARTICLE_REVIEWS {
    INTEGER id
    INTEGER article_id
    INTEGER rating
    STRING text
    STRING created_by
    TIMESTAMP created_at
  }
```

## Videos Architecture

### Videos Endpoints

- `GET /videos`
- `GET /videos/{video_id}`
- `POST /videos`

### Videos Flow Notes

- Router enforces authenticated session.
- Service validates create payloads via typed `_parse_create_payload`.
- Payloads are enriched with best-effort `preview_image_url` resolution through `UrlPreviewService`.
- Videos are first-class learning items, but the current phase intentionally keeps them lighter than courses:
  - no `/tracking` integration
  - no recommendation write model
  - no dedicated reviews API

### Videos Data Model

```mermaid
erDiagram
  USERS ||--o{ VIDEOS : "shares"
  VIDEOS {
    INTEGER id
    STRING title
    STRING description
    STRING provider
    STRING category
    STRING url
    STRING created_by
    TIMESTAMP created_at
  }
```

## Notifications Architecture

### Notifications Endpoints

- `GET /notifications/activity?scope=inbox|team&limit=...`

### Notifications Flow Notes

- Router enforces authenticated session.
- Service composes activity from repository reads of:
  - course shares
  - video shares
  - course recommendations
  - path recommendations
  - course reviews
  - path reviews
  - article reviews
- `scope=inbox`: mailbox-style feed for the current user (excludes own events).
- `scope=team`: team-wide timeline feed.
