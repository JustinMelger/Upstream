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

# Compatibility name; these are quality checks, not a baseline ratchet.
alias lint-ratchet := quality

quality: lint
    uv run lint-imports

# Tests may truncate tables. Match the browser seed command's opt-in contract.
[private]
require-test-db:
    @test "${E2E_DATABASE_IS_DISPOSABLE:-}" = 1 || { echo "Set E2E_DATABASE_IS_DISPOSABLE=1 for a disposable test database." >&2; exit 1; }
    @case "${DATABASE_URL:-}" in postgres://*/*_test|postgresql://*/*_test|postgresql+asyncpg://*/*_test) ;; *) echo "Set DATABASE_URL to a disposable PostgreSQL database ending in _test." >&2; exit 1 ;; esac

unit: require-test-db
    uv run pytest tests/backend -m unit
    npm --prefix frontend/react test

integration: require-test-db
    uv run pytest tests/backend -m integration

architecture:
    uv run lint-imports
    uv run pytest tests/backend -m architecture

architecture-sync-check:
    ./scripts/check_architecture_sync.sh

api-types:
    uv run python -m scripts.export_openapi
    npm --prefix frontend/react run api:generate

# Requires a migrated, seeded disposable browser database; see operations.md.
e2e: require-test-db
    npm --prefix frontend/react run e2e

audit:
    uv run pip-audit
    npm --prefix frontend/react audit --audit-level=moderate

# Backend/frontend checks; browser workflows use a separately prepared database.
test: require-test-db lint audit unit architecture integration

# Include contracts, production compilation and mocked Linux visual coverage.
check: test architecture-sync-check build-ui visual

alias build := build-ui

build-images:
    docker compose build

visual:
    docker build -t learning-visual -f frontend/react/Dockerfile.visual frontend/react
    mkdir -p frontend/react/test-results
    docker run --rm --ipc=host -v "$PWD/frontend/react/test-results:/app/test-results" learning-visual

build-ui:
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
