# Architecture & Coding Standards (Contributor One-Pager)

This page summarizes the architecture and coding standards used in this project.
Use it as the default guide before adding or refactoring code.

## 1) Architecture Model

### Backend
- API layer: FastAPI routers for transport concerns only.
- Service layer: business rules, validation, orchestration.
- Repository layer: persistence/query concerns only.
- Database: async SQLAlchemy + Alembic migrations.
- Transactions: `session_scope(...)` boundary (services remain transaction-agnostic).

### Frontend (NiceGUI, MVC-style)
- `pages/*/page.py`: UI composition + event binding only.
- `pages/*/controller.py` and `pages/*/orchestration.py`: flow/orchestration logic.
- `frontend/ui/nicegui/services/*`: API/use-case access and data loading.
- `pages/*/sections.py`: reusable page UI blocks.
- `pages/*/view_model.py`: UI shaping/formatting of payloads.
- `components/*`: cross-page reusable primitives.

## 2) Boundary Rules

- No direct API calls in page UI modules.
- Keep controller modules UI-framework agnostic (no `nicegui.ui` imports).
- Keep repository concerns out of routers.
- Keep persistence/session internals out of service business logic.
- Prefer typed payload parsing at service boundaries (pydantic dataclasses).

## 3) Mutation & Error Patterns

- Mutation flow standard:
  1. optimistic update
  2. rollback on failure
  3. user feedback
  4. targeted refresh (avoid full-page reloads)
- Use typed domain/app errors (`ServiceError`, `ApiError`) over broad `except Exception`.
- Use guarded UI actions and safe notifications for deleted-slot/runtime UI edge cases.

## 4) Code Quality Standards

- Keep modules focused and small; extract orchestration/sections/view-models as complexity grows.
- Reuse shared utilities/components instead of duplicating formatting/status/feedback logic.
- Use typed state/view-model structures instead of ad-hoc dict mutation in page modules.
- Keep naming explicit and consistent across backend/frontend layers.
- Keep docs aligned with implementation changes.

## 5) Test & Quality Gates

- Mark tests clearly: `unit`, `integration`, `architecture`.
- Architecture guards enforce boundaries (not just conventions).
- Add focused tests when extracting logic (controller/orchestration/view-model/service).
- Maintain lint + test gates (`ruff`, `pytest`) for touched code.

## 6) Contributor Checklist (Before PR)

- Boundary check: did you keep page/controller/service/repo responsibilities clean?
- Typing check: did new service entrypoints use typed parse helpers?
- Error check: did you avoid broad exception swallowing?
- UX check: did mutations follow optimistic/rollback/feedback/refresh pattern?
- Test check: added/updated unit + architecture tests for changed behavior?
- Docs check: do architecture docs still reflect implementation?

## 7) Source of Truth Docs

- High-level architecture: `docs/architecture.md`
- Backend architecture: `docs/architecture_backend.md`
- Frontend architecture: `docs/architecture_frontend.md`
- Frontend MVC migration status: `docs/frontend_mvc_migration.md`
- Delivery roadmap: `docs/roadmap.md`
