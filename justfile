# Format imports with ruff
fmt:
	.venv/bin/ruff check --select I --fix
	.venv/bin/ruff format --line-length 128

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

unit:
	.venv/bin/python -m pytest -m unit

integration:
	.venv/bin/python -m pytest -m integration

test: lint unit integration

watch:
	docker compose -f docker-compose.watch.yml watch
