# AGENT.md

This document defines the engineering standards for working in the Learning Hub repository.

It maps the general standards used in other projects onto this codebase's actual structure:

- FastAPI backend
- NiceGUI frontend
- async SQLAlchemy repositories
- route/controller/service architecture

The goal is to keep the codebase easy to reason about while finishing and stabilizing v1.

## 1. Core Principles

- Prefer simple, explicit code over clever abstractions.
- Keep behavior close to the domain concept that owns it.
- Push side effects to system edges.
- Optimize for readability and testability first.
- Add abstractions only when they remove real duplication or isolate real variability.
- Keep the shipped product narrower than the codebase if needed; do not preserve feature creep by default.

## 2. Repository Layering Rules

This repository is organized into these practical layers.

### Backend

- `backend/api`
  - FastAPI transport layer only.
  - Owns HTTP request/response handling, dependency injection, and auth guards.
  - Must not contain business rules beyond thin transport validation and policy checks.

- `backend/services`
  - Application and domain behavior.
  - Owns business rules, validation, orchestration, and domain errors.
  - Coordinates repositories and other focused services.

- `backend/database/async_repositories`
  - Persistence adapters only.
  - Owns SQLAlchemy queries and row serialization.
  - Must not contain domain policy or request-oriented logic.

- `backend/database/models.py`
  - Typed internal record models used across repository/service boundaries.

- `backend/database/orm_models.py`
  - SQLAlchemy ORM table mappings only.

- `backend/core`
  - Configuration, error envelopes, observability, and other framework-level concerns.

### Frontend

- `frontend/ui/nicegui/pages/*/page.py`
  - Route registration, UI composition, and event binding only.

- `frontend/ui/nicegui/pages/*/controller.py`
  - Page-level orchestration only.
  - Coordinates page-local workflows without rendering UI.

- `frontend/ui/nicegui/pages/*/orchestration.py`, `actions.py`, `transitions.py`, `ui_glue.py`, `view_model.py`
  - Focused page support modules.
  - Keep pure transforms and flow helpers here when they are page-scoped.

- `frontend/ui/nicegui/services`
  - Frontend domain/service layer.
  - Owns API/use-case access and shared orchestration that is not page-specific.

- `frontend/ui/nicegui/core`
  - Shared infrastructure: API client, config, session store, guards, navigation, common formatting.

- `frontend/ui/nicegui/components`
  - Reusable visual/UI primitives and sections.

### Tests

- `tests/backend`
  - API, service, repository, and backend architecture coverage.

- `tests/frontend`
  - page/controller/service/view-model and frontend architecture coverage.

- `tests/e2e`
  - smoke and UI-level behavior checks.

## 3. Dependency Direction Rules

- `backend/api` may depend on `backend/services`, `backend/api/schemas`, `backend/core`, and dependency/policy modules.
- `backend/services` may depend on repositories, internal models, and `backend/core`.
- repositories must not depend on services or API modules.
- ORM models must not depend on services or API modules.

- `frontend/ui/nicegui/pages/*` may depend on:
  - page-local modules
  - `components`
  - `core`
  - `services`
- `frontend/ui/nicegui/services` must not depend on `pages/*`.
- `frontend/ui/nicegui/core` must not depend on page modules.

- tests may import application code freely, but architecture tests should enforce the boundaries above.

## 4. OOP Guidelines

- Use a class only when it represents a clear concept with owned behavior.
- Prefer composition over inheritance.
- Avoid inheritance unless there is a real subtype relationship.
- Keep constructors cheap.
- Do not perform network I/O, database mutation, subprocess execution, or file writes in `__init__`.
- Prefer stateless services where possible.
- Pass dependencies explicitly via constructors or dependency providers.

Use classes for:

- backend services
- repositories
- frontend page controllers
- API clients
- stateful adapters such as session stores

Do not use classes for:

- passive namespaces
- unrelated utility grouping
- wrappers that only forward calls without adding value

## 5. Method and Module Design

- A class or module should have one clear reason to change.
- Public method names should describe outcomes, not mechanisms.
- Keep methods small enough to scan quickly.
- If branching grows large, split collaborators or extract focused helpers.
- Avoid boolean-flag-driven behavior when separate methods or focused collaborators are clearer.

Preferred names:

- `create_user`
- `create_path`
- `set_tracking_status`
- `load_course_detail_bundle`
- `delete_review`
- `resolve_metadata`

Avoid vague names such as:

- `handle`
- `process`
- `do_work`
- `manager`
- `helper`

unless the surrounding context makes the meaning precise and unavoidable.

## 6. State and Side Effects

- Keep mutation localized and explicit.
- Do not read environment variables outside config/settings modules.
  - backend: `backend/core/config.py`
  - frontend: `frontend/ui/nicegui/core/config.py`
- Do not perform direct SQL outside repository modules.
- Do not perform HTTP requests outside dedicated clients/services.
- Do not perform ad hoc file or JSON writes in business logic.
- Return typed results or explicit payload structures instead of mutating hidden global state.

## 7. Data Contracts and Types

- Use typed models at service boundaries whenever practical.
- Avoid spreading raw `dict[str, Any]` through the app when a domain model or typed payload is justified.
- Keep optional fields truly optional; do not overload empty strings as missing in new code.
- Prefer narrow types, enums, literals, or constrained strings where the domain is fixed.
- Keep conversion from external payloads to internal models at the boundary:
  - backend API schema -> service payload
  - repository row -> internal record
  - frontend API response -> frontend service/page view model

Because this repository already contains some `dict[str, Any]` flows, use this rule pragmatically:

- do not expand weakly typed flows
- improve typing when touching a boundary-heavy feature
- prefer typed parse helpers in services over adding more ad hoc dict handling

## 8. Error Handling

- Raise specific domain exceptions for domain failures.
- Do not use bare `Exception` unless re-raising at a system boundary with context.
- Keep error messages specific and actionable.
- Fail fast on invalid configuration.
- Distinguish domain decisions from operational failures.

Examples in this repository:

- missing `DATABASE_URL` is a configuration failure
- `not_found`, `invalid_payload`, `admin_required` are domain/app failures
- failed HTTP request in frontend `ApiClient` is an operational error
- failed URL metadata fetch is an operational concern, not product logic

## 9. Backend Standards

- Routers stay thin.
- Service modules own business rules and typed payload parsing.
- Repositories own query construction and persistence only.
- Request-scoped service construction belongs in `backend/api/deps.py`.
- Shared service instances are allowed only for safe, intentional cases such as cacheable support services.
- Transaction boundaries should remain explicit and minimal via session helpers.
- Policy helpers should be reused instead of duplicating authorization branches.

## 10. Frontend Standards

- Page modules stay thin and UI-focused.
- Controllers orchestrate workflows; they do not render UI.
- Shared domain fetching belongs in frontend services, not inside page closures.
- Reusable formatting and state-shaping logic belongs in `ui_glue.py`, `view_model.py`, or `core`.
- Avoid reintroducing legacy top-level routes that the product no longer treats as canonical.
- Prefer the currently registered route surface over dormant/legacy page implementations.

## 11. Naming Standards

- Use domain language from the product:
  - `course`
  - `article`
  - `video`
  - `path`
  - `review`
  - `tracking`
  - `team`
  - `session`
  - `recommendation` only where the code still intentionally owns it
- Avoid generic names such as:
  - `data`
  - `item`
  - `thing`
  - `manager`
  - `helper`
  unless the role is genuinely generic
- File names should match the main concept in the file.

## 12. Testing Standards

- Tests should mirror the source tree and layer boundaries.
- Prefer unit tests for pure logic and business rules.
- Add integration tests for API/service/repository behavior.
- Every bug fix should include a regression test when practical.
- Mock external systems at boundaries:
  - backend service or URL-fetch boundary
  - frontend API client boundary
- Prefer public behavior assertions over private implementation assertions.

Coverage priorities for this repository:

- auth and session rules
- ownership/authorization rules
- tracking and path-selection flows
- share/create/edit/delete workflows
- review behavior
- release-critical feature-flag and route behavior
- architecture boundary tests

## 13. Docstrings and Comments

- Use Google-style docstrings for public modules, classes, and functions.
- Comments should explain intent, constraints, or non-obvious behavior.
- Do not add comments that simply restate the code.
- Keep docstrings aligned with real behavior.
- When v1 scope changes, update docs and docstrings that describe product capability.

## 14. Dependency and Abstraction Discipline

- Add a dependency only if it meaningfully reduces complexity or maintenance cost.
- Prefer standard library or existing project patterns before adding new libraries.
- Introduce interfaces/protocols only where multiple implementations are realistic.
- Do not generalize early for hypothetical providers, auth modes, or UI flows.
- Do not keep weak abstractions alive just because code already exists; remove them if they blur the product or architecture.

## 15. Refactoring Rule

When adding or changing a feature:

- if the change fits the current structure cleanly, keep it simple
- if the change makes a class, route, or page noticeably harder to understand, refactor in the same change
- do not leave small, obvious structural debt in place when the fix is local
- when touching legacy/stale feature areas, prefer converging on one canonical implementation rather than preserving duplicates

## 16. Current Repository Design Direction

The intended direction for this repository is:

- backend:
  - thin routers
  - explicit service layer
  - repository-owned persistence
- frontend:
  - thin route/page modules
  - controller/service-driven orchestration
  - Explore-first canonical navigation
- product:
  - v1 is intentionally narrower than the full roadmap
  - `docs/v1/` is the release source of truth

While stabilizing v1:

- prefer removing confusion over preserving extra capability
- prefer one canonical route/page implementation per feature
- prefer “share, review, organize, track” over broad feature sprawl

## 17. Practical V1 Rule

## 17. Source Of Truth Docs

Use these docs as the primary architecture and planning references:

- `docs/v1/README.md`
  - shipped v1 product scope and release contract
- `docs/architecture_standards.md`
  - repository-wide architecture and coding standards
- `docs/architecture_improvement_plan.md`
  - staged post-v1 architecture improvement plan
- `docs/post_phase1_backlog.md`
  - deferred cleanup and refactor backlog after completed Phase 1 work
- `docs/nicegui_design_baseline.md`
  - stable layout and page-design baseline for the NiceGUI frontend
- `docs/nicegui_design_implementation_plan.md`
  - phased rollout plan for the stable NiceGUI design baseline
- `docs/app_redesign_brief.md`
  - app-wide redesign direction based on the current product model
- `docs/frontend_target_shape.md`
  - preferred target structure for NiceGUI page packages
- `docs/technical_debt_register.md`
  - explicit post-v1 technical debt register

When the codebase changes materially, keep these docs aligned with the implementation.

## 18. Practical V1 Rule

Before keeping or expanding a feature, ask:

- Is it part of `docs/v1/`?
- Is it on a canonical route or API surface?
- Is it tested at the right layer?
- Is it documented as supported behavior?
- Is it worth supporting after release?

If the answer is no, defer it, hide it, or remove it.
