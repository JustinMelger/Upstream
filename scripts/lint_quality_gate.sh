#!/usr/bin/env bash
set -euo pipefail
uv run ruff check .
uv run ruff format --check .
uv run mypy backend
uv run lint-imports
npm --prefix frontend/react run format:check
npm --prefix frontend/react run lint
npm --prefix frontend/react run typecheck
