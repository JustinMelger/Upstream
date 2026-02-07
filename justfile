# Format imports with ruff
fmt:
	uv run ruff check --select I --fix
	uv run ruff format --line-length 128

lint:
	uv run ruff check .
	uv run ruff format --check .

unit:
	uv run pytest -m unit

integration:
	uv run pytest -m integration

audit:
	uv run pip-audit

test: lint audit unit integration

watch:
	docker compose -f docker-compose.watch.yml watch
