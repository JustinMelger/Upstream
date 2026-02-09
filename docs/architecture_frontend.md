# Frontend Architecture (NiceGUI Target)

## Overview
The current UI is built with Streamlit.
If/when the UI migrates to NiceGUI, a class-based structure fits well because NiceGUI is event-driven and component-oriented.

Recommended separation:

- Pages: route handlers that compose UI and bind events.
- UI components: reusable widgets (tables, forms, dialogs).
- Frontend services: domain-specific “use cases” that orchestrate API calls and UI state updates.
- API client: typed wrapper that handles base URL, `X-Session-Token` injection, and error mapping.
- Session store: single place to manage login state, token persistence, and current-user metadata.

## NiceGUI Sequence

```mermaid
sequenceDiagram
  participant User as User
  participant UI as NiceGUI Page
  participant Store as SessionStore
  participant Client as ApiClient
  participant API as FastAPI Backend
  participant DB as Postgres

  User->>UI: Click / submit form
  UI->>Store: get_token() / set_token()
  UI->>Client: request(endpoint, token)
  Client->>API: HTTP + X-Session-Token
  API->>DB: Read/write
  DB-->>API: Result
  API-->>Client: JSON
  Client-->>UI: Parsed payload / mapped error
```

## NiceGUI Domain Overview

```mermaid
classDiagram
  class App {
    +register_routes()
    +mount_pages()
  }

  class ApiClient {
    -base_url: str
    +get(path): dict
    +post(path, payload): dict
    +put(path, payload): dict
    +delete(path): dict
  }

  class SessionStore {
    -token: str|None
    -user: dict|None
    +login(username, password): None
    +logout(): None
    +get_token(): str|None
    +current_user(): dict|None
  }

  class CoursesService {
    +list_courses(filters): list
    +create_course(payload): dict
    +update_course(id, payload): dict
    +delete_course(id): bool
  }

  class CoursesPage {
    +render()
    +bind_events()
  }

  App --> CoursesPage
  CoursesPage --> CoursesService
  CoursesService --> ApiClient
  ApiClient --> SessionStore : token
```

Notes:

- Pages should stay thin (UI composition + event handlers).
- Frontend services should contain “workflow logic” (for example refresh lists after mutations).
- `ApiClient` should be the only place that knows about HTTP and error envelopes.
