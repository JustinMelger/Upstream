# Format imports with ruff
fmt:
	ruff check --select I --fix
	ruff format --line-length 128