#!/usr/bin/env bash
set -euo pipefail

# Enforce architecture docs/guard updates when architecture-significant code changes.
# This gate is only enforced for pull_request events where a base ref is available.

if [[ "${GITHUB_EVENT_NAME:-}" != "pull_request" ]]; then
  echo "architecture-sync: non-PR context; skipping drift check"
  exit 0
fi

base_ref="${GITHUB_BASE_REF:-}"
if [[ -z "${base_ref}" ]]; then
  echo "architecture-sync: missing GITHUB_BASE_REF; skipping drift check"
  exit 0
fi

git fetch --no-tags --depth=1 origin "${base_ref}"

# Prefer merge-base diff (PR semantic). In shallow/edge CI histories, attempt to
# deepen history before deciding the check cannot run reliably.
merge_base="$(git merge-base "origin/${base_ref}" HEAD 2>/dev/null || true)"
if [[ -z "${merge_base}" ]]; then
  echo "architecture-sync: no merge base yet; attempting deeper fetch"
  git fetch --no-tags --deepen=200 origin "${base_ref}" || true
  head_ref="${GITHUB_HEAD_REF:-}"
  if [[ -n "${head_ref}" ]]; then
    git fetch --no-tags --deepen=200 origin "${head_ref}" || true
  fi
  merge_base="$(git merge-base "origin/${base_ref}" HEAD 2>/dev/null || true)"
fi

if [[ -z "${merge_base}" ]]; then
  is_shallow="$(git rev-parse --is-shallow-repository 2>/dev/null || echo false)"
  if [[ "${is_shallow}" == "true" ]]; then
    echo "architecture-sync: repository is shallow; attempting unshallow fetch"
    git fetch --no-tags --prune --unshallow || true
    git fetch --no-tags origin "${base_ref}" || true
    merge_base="$(git merge-base "origin/${base_ref}" HEAD 2>/dev/null || true)"
  fi
fi

if [[ -z "${merge_base}" ]]; then
  echo "architecture-sync: unable to determine merge base for reliable PR diff; skipping drift check"
  exit 0
fi

changed_files="$(git diff --name-only "${merge_base}..HEAD")"

if [[ -z "${changed_files}" ]]; then
  echo "architecture-sync: no changed files detected"
  exit 0
fi

architecture_code_regex='^(frontend/ui/nicegui/main\.py|frontend/ui/nicegui/pages/[^/]+/(page|controller|orchestration|route_init|reducers|view_model|state|transitions|ui_glue)\.py|frontend/ui/nicegui/core/(guards|mutation_flow|navigation|navigation_intents)\.py|backend/api/|backend/database/orm_models\.py|backend/database/async_repositories/)'
# High-impact architecture boundaries that should remain hard-gated.
architecture_code_strict_regex='^(frontend/ui/nicegui/main\.py|frontend/ui/nicegui/pages/[^/]+/(page|controller|orchestration|route_init)\.py|backend/api/|backend/database/orm_models\.py|backend/database/async_repositories/)'
architecture_contract_regex='^(docs/architecture_frontend\.md|docs/architecture_backend\.md|tests/frontend/ui/nicegui/test_architecture_docs_contracts\.py|tests/frontend/ui/nicegui/pages/.*/test_.*architecture\.py)'

code_changed=0
contract_changed=0
strict_code_changed=0
matched_code_files=()
matched_contract_files=()
matched_strict_code_files=()

while IFS= read -r file; do
  if [[ "${file}" =~ ${architecture_code_regex} ]]; then
    code_changed=1
    matched_code_files+=("${file}")
  fi
  if [[ "${file}" =~ ${architecture_code_strict_regex} ]]; then
    strict_code_changed=1
    matched_strict_code_files+=("${file}")
  fi
  if [[ "${file}" =~ ${architecture_contract_regex} ]]; then
    contract_changed=1
    matched_contract_files+=("${file}")
  fi
done <<< "${changed_files}"

if [[ "${strict_code_changed}" -eq 1 && "${contract_changed}" -eq 0 ]]; then
  echo "architecture-sync: architecture-significant code changed without docs/guard updates"
  echo "Matched strict architecture files:"
  for file in "${matched_strict_code_files[@]}"; do
    echo "  - ${file}"
  done
  echo "Please also update one of:"
  echo "  - docs/architecture_frontend.md"
  echo "  - docs/architecture_backend.md"
  echo "  - tests/frontend/ui/nicegui/test_architecture_docs_contracts.py"
  echo "  - relevant tests/frontend/ui/nicegui/pages/*/test_*architecture.py"
  exit 1
fi

if [[ "${code_changed}" -eq 1 && "${contract_changed}" -eq 0 ]]; then
  echo "architecture-sync: warning (non-strict architecture files changed without docs/guard updates)"
  echo "Matched non-strict architecture files:"
  for file in "${matched_code_files[@]}"; do
    echo "  - ${file}"
  done
  echo "No hard failure because strict architecture boundary files were not changed."
  exit 0
fi

echo "architecture-sync: OK"
