# Format imports with ruff
default_database_url := "postgresql+asyncpg://learning_platform:learning_platform@127.0.0.1:5432/learning_platform"
DATABASE_URL := env_var_or_default("DATABASE_URL", default_database_url)

fmt:
	uv run ruff check --select I --fix
	uv run ruff format --line-length 128

lint:
	uv run ruff check .
	uv run ruff format --check .

unit:
	DATABASE_URL={{DATABASE_URL}} uv run pytest -m unit

integration:
	DATABASE_URL={{DATABASE_URL}} uv run pytest -m integration

audit:
	uv run pip-audit

test: lint audit unit integration

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
