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

- [x] Fix auth username normalization so login, session creation, and user lookup use one canonical identifier.
- [x] Decide the v1 status of URL metadata/preview fetching:
  - [x] harden the feature against SSRF and keep it enabled
  - [ ] or disable it for v1
- [x] Run backend regression validation on the kept v1 API surface:
  - [x] auth
  - [x] courses
  - [x] articles
  - [x] videos
  - [x] paths
  - [x] tracking
  - [x] teams
- [x] Run frontend regression validation on the kept v1 UI surface:
  - [x] login
  - [x] explore
  - [x] share item
  - [x] share path
  - [x] teams
  - [x] profile/home
  - [x] admin users
- [x] Run smoke validation for the main end-to-end flows:
  - [x] canonical smoke checklist added at `docs/v1/smoke_test_checklist.md`
  - [x] login
  - [x] share a learning item
  - [x] create a path
  - [x] track a course
  - [x] create a team and add a member
- [x] Confirm one canonical `/teams` implementation in the frontend.
- [x] Remove, archive, or clearly ignore duplicate/non-canonical `/teams` page code.
- [x] Freeze release feature flags and defaults:
  - [x] decide whether `FEATURE_AI_CURATOR` is off by default for release
  - [x] decide whether URL metadata/autofill remains enabled
- [x] Hide or remove recommendation UI from the released frontend.
- [x] Decide whether recommendation backend APIs stay dormant for now or are removed before release.
- [x] Align docs with the actual v1 feature set:
  - [x] README
  - [x] `docs/v1/*`
  - [x] roadmap wording where needed
  - [x] any UI copy that overpromises capability symmetry
- [x] Enforce single-item-per-URL invariants across learning-item types:
  - [x] reject duplicate article URLs on create
  - [x] add regression tests for article duplicate-url handling
- [x] Fix remaining shipped-page dead/broken controls:
  - [x] make Teams inbox render without requiring a selected team
  - [x] remove or wire the dead `Team settings` button on `/teams`
- [x] Enforce path data invariants in the backend:
  - [x] reject duplicate learning-item references within one path on create
  - [x] reject duplicate learning-item references within one path on update
  - [x] add regression tests for duplicate path-item refs

## P1: Strongly Recommended Before Release

- [x] Add or update tests that directly cover the auth normalization fix.
- [x] Add or update tests for the URL metadata security decision.
- [x] Verify the learning-item capability model is consistent everywhere:
  - [x] course supports tracking + reviews
  - [x] article supports reviews only
  - [x] video supports reviews only
- [x] Audit release copy so Teams is described as a basic workspace, not a full collaboration platform.
- [x] Review navigation and route exposure to ensure deferred features are not presented as core product capabilities.
- [x] Write short release notes that reflect the scoped v1 product, not the full roadmap.
- [x] Create a cleanup plan for recommendation backend/data removal if the team decides not to keep dormant APIs after release.
- [x] Align learning-item review routes across content types:
  - [x] return `404 not_found` for missing article review parents on list/create
  - [x] return `404 not_found` for missing video review parents on list/create
  - [x] add regression tests for missing article/video parent review routes
- [x] Fix shared learning-item surface consistency:
  - [x] keep shared course rows canonical as `course` instead of inferring subtype from URL/provider
  - [x] load/display article review summaries on shared learning-item surfaces
- [x] Align Home review-queue behavior with actual review-capable content:
  - [x] decide whether article/video reviews should contribute to Home pending-review counts in v1
  - [x] either include article/video review prompts or explicitly scope Home review prompts to tracked courses/selected paths only
- [x] Fix path selection state refresh so seeded course tracking appears immediately after selecting a path.
- [x] Align path API payloads with frontend expectations for freshness/sorting metadata:
  - [x] decide whether `created_at` / `updated_at` should be returned for path list/detail payloads in v1
  - [x] remove or defer frontend freshness/newest logic if timestamps stay out of the API
- [x] Align path share publish UX with the other share flows:
  - [x] decide whether path publish should return to `/explore?tab=paths` after success
  - [x] keep publish success/redirect behavior consistent across course/article/video/path

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

- [x] AI Curator:
  - [x] deferred from v1
  - [ ] included as experimental only
- [x] URL metadata/autofill:
  - [x] enabled and hardened
  - [ ] disabled for v1
- [x] Teams positioning:
  - [x] basic workspace only
  - [x] broader collaboration not promised in v1
- [x] Canonical release source of truth:
  - [x] `docs/v1/`
  - [x] roadmap treated as post-v1 strategy

## Release Exit

V1 is ready to ship only when:

- [x] all `P0` items are completed
- [x] every `P1` item is either completed or explicitly deferred
- [x] deferred features are not presented as core release scope
- [x] release notes match the shipped product
