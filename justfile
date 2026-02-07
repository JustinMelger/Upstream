# Format imports with ruff
fmt:
	ruff check --select I --fix
	ruff format --line-length 128

lint:
	ruff check .
	ruff format --check .

unit:
	pytest -m unit

integration:
	pytest -m integration

test: lint unit integration

watch:
	docker compose -f docker-compose.watch.yml watch
