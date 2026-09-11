#!/usr/bin/env bash
set -euo pipefail
uv run lint-imports
uv run python -m scripts.export_openapi --check
npm --prefix frontend/react run api:generate
git diff --exit-code -- frontend/react/src/lib/api/generated.ts
