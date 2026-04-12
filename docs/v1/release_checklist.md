# V1 Release Checklist

This is the operational checklist for closing out Learning Hub v1.

Use this file for release execution.
Use `docs/v1/README.md` for scope definition.
Use `docs/roadmap.md` for post-v1 strategy.

## Priority Key

- `P0`: must be completed before release
- `P1`: should be completed before release if time allows, otherwise explicitly deferred
- `P2`: post-v1 backlog

## P0: Release Blockers

- [ ] Fix auth username normalization so login, session creation, and user lookup use one canonical identifier.
- [ ] Decide the v1 status of URL metadata/preview fetching:
  - [ ] harden the feature against SSRF and keep it enabled
  - [ ] or disable it for v1
- [ ] Run backend regression validation on the kept v1 API surface:
  - [ ] auth
  - [ ] courses
  - [ ] articles
  - [ ] videos
  - [ ] paths
  - [ ] tracking
  - [ ] teams
- [ ] Run frontend regression validation on the kept v1 UI surface:
  - [ ] login
  - [ ] explore
  - [ ] share item
  - [ ] share path
  - [ ] teams
  - [ ] profile/home
  - [ ] admin users
- [ ] Run smoke validation for the main end-to-end flows:
  - [ ] login
  - [ ] share a learning item
  - [ ] create a path
  - [ ] track a course
  - [ ] create a team and add a member
- [ ] Confirm one canonical `/teams` implementation in the frontend.
- [ ] Remove, archive, or clearly ignore duplicate/non-canonical `/teams` page code.
- [ ] Freeze release feature flags and defaults:
  - [ ] decide whether `FEATURE_AI_CURATOR` is off by default for release
  - [ ] decide whether URL metadata/autofill remains enabled
- [ ] Hide or remove recommendation UI from the released frontend.
- [ ] Decide whether recommendation backend APIs stay dormant for now or are removed before release.
- [ ] Align docs with the actual v1 feature set:
  - [ ] README
  - [ ] `docs/v1/*`
  - [ ] roadmap wording where needed
  - [ ] any UI copy that overpromises capability symmetry

## P1: Strongly Recommended Before Release

- [ ] Add or update tests that directly cover the auth normalization fix.
- [ ] Add or update tests for the URL metadata security decision.
- [ ] Verify the learning-item capability model is consistent everywhere:
  - [ ] course supports tracking + reviews
  - [ ] article supports reviews only
  - [ ] video supports reviews only
- [ ] Audit release copy so Teams is described as a basic workspace, not a full collaboration platform.
- [ ] Review navigation and route exposure to ensure deferred features are not presented as core product capabilities.
- [ ] Write short release notes that reflect the scoped v1 product, not the full roadmap.
- [ ] Create a cleanup plan for recommendation backend/data removal if the team decides not to keep dormant APIs after release.

## P2: Explicit Post-V1 Backlog

- [ ] Auth enhancements (`Phase 3b`)
  - [ ] invite-code login
  - [ ] OAuth / SSO
  - [ ] admin allowlist
- [ ] Media pipeline expansion (`11A.3`)
  - [ ] richer thumbnail resolution
  - [ ] metadata persistence
  - [ ] quality gate
  - [ ] fallback thumbnail policy
- [ ] Activity feed v2
- [ ] Broader reliability/accessibility expansion beyond release blockers
- [ ] Strict visual-regression enforcement in CI
- [ ] Team-scoped audience sharing and collaboration model
- [ ] Review requests and discussions
- [ ] AI curator expansion beyond draft-only planning
- [ ] Recommendation feature reconsideration after v1, if real product demand appears
- [ ] Visual-system and motion polish work
- [ ] Pilot/user-testing work

## Release Decisions

Record the decisions here before release:

- [ ] AI Curator:
  - [ ] deferred from v1
  - [ ] included as experimental only
- [ ] URL metadata/autofill:
  - [ ] enabled and hardened
  - [ ] disabled for v1
- [ ] Teams positioning:
  - [ ] basic workspace only
  - [ ] broader collaboration not promised in v1
- [ ] Canonical release source of truth:
  - [ ] `docs/v1/`
  - [ ] roadmap treated as post-v1 strategy

## Release Exit

V1 is ready to ship only when:

- [ ] all `P0` items are completed
- [ ] every `P1` item is either completed or explicitly deferred
- [ ] deferred features are not presented as core release scope
- [ ] release notes match the shipped product
