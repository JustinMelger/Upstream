#!/usr/bin/env bash
set -euo pipefail

RANGE="${1:-HEAD~1..HEAD}"

CHANGED_PY="$(git diff --name-only "$RANGE" -- '*.py' | grep -E '^(backend|frontend)/' || true)"
if [ -z "$CHANGED_PY" ]; then
  echo "No changed backend/frontend Python files for ratchet checks."
else
  echo "Changed Python files:"
  echo "$CHANGED_PY"
  uv run ruff check $CHANGED_PY
  uv run mypy $CHANGED_PY
fi

echo "Running strict ruff profile on core quality scope..."
uv run ruff check backend/services frontend/ui/nicegui/core frontend/ui/nicegui/services \
  --config "lint.mccabe.max-complexity=9" \
  --config "lint.pylint.max-args=7" \
  --config "lint.pylint.max-branches=6" \
  --config "lint.pylint.max-statements=30" \
  --config "lint.pylint.max-returns=7" \

echo "Running strict mypy profile on core quality scope..."
uv run mypy frontend/ui/nicegui/core --strict
