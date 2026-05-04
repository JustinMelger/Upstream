# Architecture Improvement Plan

This document defines the first post-v1 engineering improvement plan for Learning Hub.

The goal is to improve consistency, maintainability, and architectural clarity without rewriting the application or destabilizing the shipped v1 product.

## Why This Exists

The v1 codebase is good enough to release, but it still shows the history of feature creep and iterative cleanup.

The main weak points are:

- some modules still carry legacy refactor residue
- frontend page architecture is cleaner, but still uneven by area
- some UI orchestration still lives in page files rather than clean application/presentation boundaries
- some naming and helper APIs still reflect older feature shapes
- Teams, Home, Profile, and activity-related surfaces evolved incrementally and are less cohesive than the rest of the app

This plan is intentionally incremental. It is not a rewrite plan.

## Principles

- protect the shipped v1 behavior first
- prefer local refactors over broad architectural churn
- remove dead or legacy code before introducing new abstractions
- standardize repeated patterns only after they are clearly repeated
- keep page rendering declarative and move orchestration to controllers/services
- avoid mixing feature work with broad cleanup in the same change unless the cleanup is small and local

## Workstreams

### 1. Legacy Residue Cleanup

Goal:
- remove obsolete APIs, dead wrappers, stale helper signatures, and naming that no longer matches the shipped app

Scope:
- delete stale or duplicate helpers left behind by route/page refactors
- remove unused callback parameters and generic section contracts that no longer provide value
- clean legacy docstrings and comments that still reference removed routes or old product language
- normalize older helper names so they reflect the current product model

Success criteria:
- fewer helpers that accept parameters they do not use
- fewer modules that are technically live but conceptually obsolete
- less ambiguity around which implementation path is canonical

### 2. Frontend Page Shape Normalization

Goal:
- make the main frontend surfaces follow one target page structure

Target shape:
- `page.py`: route wiring and high-level page assembly only
- `controller.py`: async workflows and mutation orchestration
- `view_model.py` / `reducers.py`: derived UI state, sorting, filtering, normalization
- `sections.py`: render composition
- `components/*`: reusable UI primitives used across pages

Priority order:
1. Teams
2. Profile
3. Home
4. remaining detail surfaces
5. any older section-heavy modules that still blur boundaries

Success criteria:
- fewer API calls or mutation flows buried inside render functions
- consistent page organization across the main app surfaces
- easier onboarding for contributors because page structure is predictable

### 3. Presentation vs Application Boundary Cleanup

Goal:
- reduce UI orchestration in render code and make mutation behavior more uniform

Scope:
- move mutation sequencing out of page render functions and into controllers/services
- standardize post-mutation refresh behavior
- reuse shared action helpers for review, tracking, share, and delete flows where the contract is truly common
- keep render functions focused on composition, not API sequencing

Success criteria:
- page rendering stays mostly declarative
- create/edit/delete/review/track flows follow clearer, shared contracts
- fewer cross-surface inconsistencies after mutations

### 4. Naming and Helper API Cleanup

Goal:
- make the code read like the actual product

Scope:
- rename helpers that still reflect removed features or old concepts
- tighten helper signatures so they accept only what they use
- remove generic names where the role is no longer generic
- align file names and public function names with the dominant concept in the file

Success criteria:
- fewer misleading or over-generic names
- less need to inspect implementation just to understand a helper’s purpose

### 5. Activity / Teams / Home / Profile Cohesion

Goal:
- make the activity-related parts of the app feel like one intentional subsystem

Working model:
- Home = personal next-step dashboard
- Teams = group activity and follow-up workspace
- Profile = personal and team stats surface
- Explore = global discovery surface

Scope:
- document and enforce what each surface owns
- remove duplicated or competing concepts across Home, Teams, and Profile
- normalize navigation and copy where the same activity concept appears in multiple places
- keep Teams positioned as a shared activity lens, not a private content silo

Success criteria:
- less cross-surface duplication
- clearer ownership of stats, activity, and follow-up concepts
- fewer UX inconsistencies caused by different surfaces evolving separately

## Delivery Phases

### Phase 1: Stabilization Cleanup

Focus:
- dead code removal
- stale helper/API cleanup
- naming cleanup
- docstring/comment cleanup

Rules:
- no broad behavior changes
- keep fixes small and local

### Phase 2: Frontend Structure Pass

Focus:
- normalize page architecture
- move orchestration out of page render files
- standardize mutation-refresh patterns

Rules:
- change one page area at a time
- keep tests updated with each extraction

### Phase 3: Activity Domain Pass

Focus:
- align Teams, Home, Profile, and activity semantics
- reduce duplicate concepts and cross-surface drift
- document the subsystem clearly

Rules:
- no major product-model changes without docs updates
- preserve the v1 rule that Explore visibility is global and Teams provide context/activity

Reference:
- [Activity Domain Restructuring](./activity_domain_restructuring.md)

### Phase 4: Optional Deeper Refactor

Focus:
- shared detail-page patterns
- clearer typed frontend contracts
- deeper controller/service cleanup where repeated pain remains

Rules:
- only do this if the earlier phases reveal stable repeated patterns
- do not invent abstractions preemptively

## Explicit Non-Goals

- rewriting the frontend architecture wholesale
- changing the v1 product model before post-release learning
- introducing new layers just to look cleaner on paper
- mixing major feature work and broad refactors in the same change

## Expected Outputs

- cleaner module boundaries
- clearer page structure across the frontend
- lower contributor confusion around canonical flows
- smaller blast radius for future features
- a healthier base for v1.1 and v2 work

## Road To v2

This section translates the general improvement plan into a concrete execution order.

The project does not need reinvention. It needs consolidation:

- finish the major systems that are still evolving
- remove rule drift between product, API, UI, tests, and docs
- raise the consistency floor across weaker surfaces
- make future regressions harder through better contracts and guardrails

### foundation for v2

These are the highest-leverage items. They directly improve product trust, architectural cohesion, and release confidence.

#### 1. Finish the auth and identity story

Goal:
- move from evolving local auth toward a stable external identity model without breaking existing users

Scope:
- implement Pocket ID OIDC support
- add local identity-link persistence
- support safe first-login linking for existing users
- define fallback/deprecation rules for local password login
- preserve the current internal session model during migration

Reference:
- [Pocket ID OIDC Design And Migration](./pocket_id_oidc_migration.md)

Success criteria:
- auth no longer feels like a temporary subsystem
- existing users can migrate without duplicate-account confusion
- login behavior is documented, testable, and rollout-safe

#### 2. Lock down product visibility and permission rules

Goal:
- make access rules explicit and consistent across the system

Scope:
- document what is personal, team-visible, and globally visible
- align API enforcement with UI visibility
- remove remaining contradictions between docs and shipped behavior
- treat aggregate stats, team visibility, and content discoverability as product rules rather than page-local decisions

Success criteria:
- no user-visible permission surprises
- docs, tests, and behavior agree
- visibility rules can be described in one short canonical matrix

#### 3. Add stronger permission and contract tests

Goal:
- prevent regressions in ownership, visibility, and auth semantics

Scope:
- add a focused matrix of who can view/edit/delete/share/review/select each major resource
- add tests for aggregate/team stats visibility
- add tests that lock auth migration behavior once OIDC is implemented

Success criteria:
- common permission regressions fail fast in CI
- product rules stop drifting silently

#### 4. Run a UX consistency pass across core surfaces

Goal:
- make the weakest key screens feel as intentional as the strongest ones

Priority surfaces:
1. Explore
2. Profile
3. Teams
4. Share
5. detail pages

Scope:
- remove layout drift
- standardize empty/loading/error states
- normalize CTA patterns and card/list behavior
- clean up wording leftovers from earlier admin-oriented product shapes

Success criteria:
- no major surface feels like it belongs to a different app
- fallback states look deliberate rather than incidental

#### 5. Reduce duplicated business-rule interpretation

Goal:
- stop multiple layers from each partially re-deciding the same rule

Scope:
- centralize ownership/visibility/auth helper behavior where possible
- reduce page- or router-local rule variations
- keep docs and architecture guards aligned with the canonical rule path

Success criteria:
- fewer “frontend says X, backend says Y” corrections
- smaller blast radius when rules change

### v2 hardening

These items deepen maintainability and production readiness after the highest-risk product and auth concerns are settled.

#### 6. Formalize identity, ownership, and audience models

Goal:
- make the data model read like the real product model

Scope:
- clarify users vs identities
- clarify creator/owner semantics
- clarify team membership vs global visibility
- reduce legacy seams in naming and persistence design

Success criteria:
- identity and ownership concepts are easy to explain to a new contributor

#### 7. Strengthen operational confidence

Goal:
- make rollout and maintenance feel designed rather than accumulated

Scope:
- improve auth rollout notes and migration safety
- tighten env-var and deployment docs
- standardize failure behavior around metadata loading, auth handshakes, and background fetches
- keep observability and CI signals aligned with product-critical flows

Success criteria:
- fewer manual “tribal knowledge” steps for deploy/debug operations

#### 8. Treat docs as product and architecture contracts

Goal:
- make docs part of the system, not just commentary on it

Scope:
- maintain short canonical docs for auth, permissions, visibility, and activity semantics
- keep architecture docs aligned with tests and route behavior
- update docs as part of rule changes, not after them

Success criteria:
- contributors can trust the main docs to describe reality

#### 9. Raise the weakest UI surfaces, not only the flagship ones

Goal:
- improve the UX floor across the app

Scope:
- identify the most awkward or inconsistent screens
- prioritize finishing passes on lower-attention surfaces
- ensure design polish is broad, not isolated

Success criteria:
- overall app quality feels even, not patchy

#### 10. Trim remaining complexity hotspots

Goal:
- reduce areas where maintenance still feels heavier than it should

Scope:
- continue moving orchestration out of render code
- tighten helper signatures
- reduce older `dict[str, Any]` boundary shapes in high-churn areas
- remove stale or low-value abstractions

Success criteria:
- common changes feel easier and safer than they do today

### post-v2 refinements

These are worthwhile after the project’s core rules and architecture are more settled.

#### 11. Add a canonical permission matrix doc

Goal:
- provide one compact reference for all major access rules

Suggested shape:
- resource
- action
- self
- authenticated user
- owner
- team member
- admin

#### 12. Expand smoke coverage for core user journeys

Priority journeys:
- login/logout
- share item/path
- review content
- select/track path
- view profile team totals
- team membership and visibility

#### 13. Standardize empty/loading/error copy system-wide

Goal:
- make fallback states feel product-designed

#### 14. Add targeted boundary comments around hard subsystems

Good candidates:
- auth/session/linking logic
- visibility/ownership enforcement boundaries
- mixed-item path persistence rules

#### 15. Maintain a lightweight release-quality checklist

Suggested checks:
- docs aligned
- permissions verified
- migrations safe
- CI green
- key fallback states reviewed
- no temporary rollout logic left undocumented

## Recommended Sequencing

If the goal is the biggest step-change in quality, use this order:

1. Pocket ID OIDC plus existing-user migration
2. visibility and permission rule consolidation
3. permission/contract test matrix
4. Explore/Profile/Teams UX consistency pass
5. operational and docs hardening

## What “9/10” Looks Like

The project reaches the next quality tier when:

- auth is stable and migration-safe
- visibility and ownership rules are boringly consistent
- the weakest key screens still feel deliberate
- docs describe reality without caveats
- future changes mostly extend the product instead of correcting drift

## Actionable Checklist

- [Post-Phase-1 Backlog](./post_phase1_backlog.md)
- [Activity Domain Restructuring](./activity_domain_restructuring.md)
