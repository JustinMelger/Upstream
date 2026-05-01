#!/usr/bin/env bash
set -euo pipefail

RANGE="${1:-HEAD~1..HEAD}"

echo "Quality gate range: $RANGE"

CHANGED_PY="$(
  git diff --name-only "$RANGE" -- '*.py' \
    | grep -E '^(backend|frontend)/' \
    || true
)"

EXISTING_CHANGED_PY="$(
  while IFS= read -r path; do
    if [ -n "$path" ] && [ -f "$path" ]; then
      echo "$path"
    fi
  done <<< "$CHANGED_PY"
)"

if [ -z "$EXISTING_CHANGED_PY" ]; then
  echo "No changed backend/frontend Python files."
  echo "Skipping Python ratchet and strict core checks."
  exit 0
fi

echo "Changed Python files:"
echo "$EXISTING_CHANGED_PY"

echo "Running ruff on changed Python files..."
uv run ruff check $EXISTING_CHANGED_PY

echo "Running mypy on changed Python files..."
uv run mypy $EXISTING_CHANGED_PY

echo "Running strict ruff profile on core quality scope..."
uv run ruff check \
  backend/services \
  frontend/ui/nicegui/core \
  frontend/ui/nicegui/services \
  --config "lint.mccabe.max-complexity=9" \
  --config "lint.pylint.max-args=7" \
  --config "lint.pylint.max-branches=6" \
  --config "lint.pylint.max-statements=30" \
  --config "lint.pylint.max-returns=7"

echo "Running strict mypy profile on core quality scope..."
uv run mypy frontend/ui/nicegui/core --strict

echo "Quality gate passed."