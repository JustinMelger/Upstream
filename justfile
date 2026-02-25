# Format imports with ruff
default_database_url := "postgresql+asyncpg://learning_platform:learning_platform@127.0.0.1:5432/learning_platform"
DATABASE_URL := env_var_or_default("DATABASE_URL", default_database_url)
default_backend_url := "http://127.0.0.1:8000"
BACKEND_URL := env_var_or_default("BACKEND_URL", default_backend_url)

fmt:
	uv run ruff check --select I --fix
	uv run ruff format --line-length 128

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-ratchet range='HEAD~1..HEAD':
	./scripts/lint_quality_gate.sh '{{range}}'

unit:
	DATABASE_URL={{DATABASE_URL}} uv run pytest -m unit

architecture:
	DATABASE_URL={{DATABASE_URL}} uv run pytest -m architecture

architecture-sync-check:
	./scripts/check_architecture_sync.sh

frontend-arch-guards:
	uv run pytest tests/frontend/ui/nicegui/test_page_package_exports.py tests/frontend/ui/nicegui/test_page_package_layout.py

integration:
	DATABASE_URL={{DATABASE_URL}} uv run pytest -m integration

e2e:
	E2E_API_URL=http://127.0.0.1:8000 E2E_UI_URL=http://127.0.0.1:8080 uv run pytest tests/e2e -m e2e

e2e-update-baselines:
	E2E_API_URL=http://127.0.0.1:8000 E2E_UI_URL=http://127.0.0.1:8080 E2E_UPDATE_VISUAL_BASELINES=1 uv run pytest tests/e2e -m e2e

audit:
	uv run pip-audit

test: lint audit unit architecture integration

watch:
	docker compose -f docker-compose.watch.yml watch

db-up:
	docker compose up -d postgres

db-wait:
	#!/usr/bin/env bash
	set -euo pipefail
	for i in {1..40}; do
		if docker compose exec -T postgres pg_isready -U learning_platform -d learning_platform >/dev/null 2>&1; then
			exit 0
		fi
		sleep 0.5
	done
	echo "postgres not ready after 20s" >&2
	exit 1

migrate: db-wait
	DATABASE_URL={{DATABASE_URL}} uv run alembic upgrade head

db-init: db-up db-wait migrate

ui:
	BACKEND_URL={{BACKEND_URL}} uv run python -m frontend.ui.nicegui.main

backend:
	DATABASE_URL={{DATABASE_URL}} uv run uvicorn backend.main:app --reload --port 8000

dev: db-init
	@echo "Starting backend + UI (Ctrl+C stops the foreground process; you may need to stop the other one separately)."
	just backend & just ui
