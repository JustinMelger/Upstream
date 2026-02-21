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

# Prefer merge-base diff (PR semantic), but gracefully degrade in shallow/edge CI histories
# where `origin/<base>...HEAD` has no merge base.
merge_base="$(git merge-base "origin/${base_ref}" HEAD 2>/dev/null || true)"
if [[ -n "${merge_base}" ]]; then
  changed_files="$(git diff --name-only "${merge_base}..HEAD")"
else
  echo "architecture-sync: no merge base for origin/${base_ref} and HEAD; using direct base-vs-head diff fallback"
  changed_files="$(git diff --name-only "origin/${base_ref}" HEAD)"
fi

if [[ -z "${changed_files}" ]]; then
  echo "architecture-sync: no changed files detected"
  exit 0
fi

architecture_code_regex='^(frontend/ui/nicegui/pages/|frontend/ui/nicegui/core/(guards|mutation_flow|navigation|navigation_intents)\.py|backend/api/|backend/database/orm_models\.py|backend/database/async_repositories/)'
architecture_contract_regex='^(docs/architecture_frontend\.md|docs/architecture_backend\.md|tests/frontend/ui/nicegui/test_architecture_docs_contracts\.py|tests/frontend/ui/nicegui/pages/.*/test_.*architecture\.py)'

code_changed=0
contract_changed=0

while IFS= read -r file; do
  if [[ "${file}" =~ ${architecture_code_regex} ]]; then
    code_changed=1
  fi
  if [[ "${file}" =~ ${architecture_contract_regex} ]]; then
    contract_changed=1
  fi
done <<< "${changed_files}"

if [[ "${code_changed}" -eq 1 && "${contract_changed}" -eq 0 ]]; then
  echo "architecture-sync: architecture-significant code changed without docs/guard updates"
  echo "Please also update one of:"
  echo "  - docs/architecture_frontend.md"
  echo "  - docs/architecture_backend.md"
  echo "  - tests/frontend/ui/nicegui/test_architecture_docs_contracts.py"
  echo "  - relevant tests/frontend/ui/nicegui/pages/*/test_*architecture.py"
  exit 1
fi

echo "architecture-sync: OK"
