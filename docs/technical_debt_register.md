# Technical Debt Register

This document tracks the main architectural and structural debt items accepted after the v1 release.

The intent is to keep debt explicit and prioritized instead of letting it remain as vague background discomfort.

## P1: Legacy Refactor Residue

Problem:
- some modules and helper APIs still reflect earlier route shapes, removed flows, or partial refactors

Examples:
- stale helper signatures
- legacy naming
- older docstrings/comments that do not match the shipped app model

Impact:
- contributor confusion
- harder code review
- unnecessary coupling between modules

Planned action:
- remove stale APIs and names during stabilization cleanup

## P1: Uneven Frontend Package Shape

Problem:
- page areas do not yet follow one consistent structure

Impact:
- harder navigation of the codebase
- different expectations from one page package to another
- more render/orchestration mixing than necessary

Planned action:
- normalize page shape toward the target structure in `docs/frontend_target_shape.md`

## P1: UI Orchestration Still Present In Render Code

Problem:
- some render paths still mix layout, mutation sequencing, refresh logic, and navigation

Impact:
- more fragile UI behavior
- harder testing
- repeated post-mutation inconsistency risk

Planned action:
- move repeated mutation flows into controllers/actions/services
- keep render functions more declarative
- see `docs/post_phase1_backlog.md`

## P2: Naming Drift From Feature Creep

Problem:
- some helper/file/function names reflect old product language or temporary abstractions

Impact:
- lower readability
- slower onboarding
- misleading APIs that accept more than they need

Planned action:
- tighten naming and signatures during routine refactors
- see `docs/post_phase1_backlog.md`

## P2: Activity Subsystem Cohesion

Problem:
- Teams, Home, Profile, and activity-related concepts evolved incrementally and are not yet as cohesive as Explore

Impact:
- duplicated concepts
- weaker mental model for contributors
- higher chance of cross-surface UX drift

Planned action:
- run an activity-domain pass after stabilization cleanup
- see `docs/activity_domain_restructuring.md`
- see `docs/post_phase1_backlog.md`

## P3: Shared Detail-Page Patterns

Problem:
- detail pages are much more aligned now, but still not driven by a clearly shared architecture

Impact:
- future divergence risk
- repeated review/action/sidebar logic

Planned action:
- only extract stronger shared patterns if repeated maintenance pain remains after v1
- see `docs/post_phase1_backlog.md`

## P3: Older Untyped Payload Boundaries

Problem:
- some older areas still pass `dict[str, Any]` payloads across controller/service/view-model boundaries

Impact:
- weaker contracts
- more defensive parsing at callsites
- harder future refactors in activity, detail bundles, and stats projections

Planned action:
- expand typed boundary models incrementally
- see `docs/post_phase1_backlog.md`

## Not Planned As Immediate Work

These are intentionally not first-wave refactors:

- a wholesale frontend rewrite
- replacing NiceGUI page structure with a new framework pattern
- introducing abstract interfaces for hypothetical future UIs
- major domain-model changes to Explore/Teams visibility before post-release learning
