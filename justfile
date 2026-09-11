set dotenv-load

default:
    @just --list

fmt:
    uv run ruff check --select I --fix backend tests scripts alembic
    uv run ruff format backend tests scripts alembic
    npm --prefix frontend/react run format

lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy backend
    npm --prefix frontend/react run format:check
    npm --prefix frontend/react run lint
    npm --prefix frontend/react run typecheck

lint-ratchet:
    ./scripts/lint_quality_gate.sh

unit:
    uv run pytest tests/backend -m unit
    npm --prefix frontend/react test

integration:
    uv run pytest tests/backend -m integration

architecture:
    uv run lint-imports
    uv run pytest tests/backend -m architecture

architecture-sync-check:
    ./scripts/check_architecture_sync.sh

api-types:
    uv run python -m scripts.export_openapi
    npm --prefix frontend/react run api:generate

e2e:
    npm --prefix frontend/react run e2e

audit:
    uv run pip-audit
    npm --prefix frontend/react audit --audit-level=moderate

test: lint audit unit architecture integration

build:
    npm --prefix frontend/react run build

watch:
    docker compose -f docker-compose.yml -f docker-compose.watch.yml up --watch

db-up:
    docker compose up -d postgres

migrate:
    uv run alembic upgrade head

ui:
    npm --prefix frontend/react run dev

backend:
    uv run uvicorn backend.main:app --reload --port 8000
