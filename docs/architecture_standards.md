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
- Keep frontend dependency direction one-way:
  - Page layer can depend on services/core/components through controllers/actions.
  - Service layer must never import from page modules.
  - Move shared transforms/parsers to `frontend/ui/nicegui/services/*` or `frontend/ui/nicegui/core/*`.
- Keep repository concerns out of routers.
- Keep persistence/session internals out of service business logic.
- Prefer typed payload parsing at service boundaries (pydantic dataclasses).
- For paths, treat ordered typed `items` (`type`, `id`, `position`) as the mutation contract.

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
- Terminology model for cards/detail dialogs:
  - use `Open details` for detail-view actions,
  - use `Open source` for external-link actions,
  - use `Manage in Paths` for path-management deep-link actions,
  - use `Shared by ...` as the ownership/byline label.
- Lint thresholds (repo baseline ratchet): `C901<=19`, `PLR0913<=10`, `PLR0912<=14`, `PLR0915<=70`, `PLR0911<=8`.
- Strict complexity profile for core scope (`backend/services`, `frontend/ui/nicegui/core`, `frontend/ui/nicegui/services`):
  `C901<=9`, `PLR0913<=7`, `PLR0912<=6`, `PLR0915<=30`.
- Type-checking: keep scoped `mypy` gate on service/core modules, enforce `mypy --strict` on
  `frontend/ui/nicegui/core`, and require typed defs across application code by default.
  Temporary opt-out is limited to legacy transport entrypoints in `backend.api.*` and `backend.main`.
  Note: scoped strict-core `ruff` thresholds still live in the quality-gate script because Ruff cannot express
  different complexity thresholds for different module scopes in one project config file, and the strict core
  `mypy` invocation also remains script-driven for now.
- Docstring enforcement (Ruff + pydocstyle, Google convention):
  - Enforced rules:
    - `D102`: public methods require docstrings.
    - `D103`: public functions require docstrings.
    - `D107`: `__init__` methods require docstrings.
  - Scope:
    - enforced for application code in `frontend/` and `backend/`.
    - intentionally ignored for `tests/**/*.py` and `scripts/**/*.py` to keep CI noise low while preserving strong standards in shipped code.
    - intentionally ignored for `alembic/**/*.py` because migrations are one-off delivery artifacts rather than maintained app modules.

## 5) Test & Quality Gates

- Mark tests clearly: `unit`, `integration`, `architecture`.
- Architecture guards enforce boundaries (not just conventions).
- Required boundary guard coverage:
  - `tests/frontend/ui/nicegui/test_architecture_docs_contracts.py` for global page/service guardrails.
  - `tests/frontend/ui/nicegui/pages/explore/test_explore_architecture.py` for Explore package boundaries.
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
- Post-v1 architecture improvement plan: `docs/architecture_improvement_plan.md`
- Stable NiceGUI design baseline: `docs/nicegui_design_baseline.md`
- NiceGUI design implementation plan: `docs/nicegui_design_implementation_plan.md`
- App redesign brief: `docs/app_redesign_brief.md`
- V1 product spec: `docs/v1/README.md`
- Backend architecture: `docs/architecture_backend.md`
- Frontend architecture: `docs/architecture_frontend.md`
- Frontend target shape: `docs/frontend_target_shape.md`
- Technical debt register: `docs/technical_debt_register.md`
- Delivery roadmap: `docs/roadmap.md`
