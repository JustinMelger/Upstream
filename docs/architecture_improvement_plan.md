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

## Actionable Checklist

- [Post-Phase-1 Backlog](./post_phase1_backlog.md)
- [Activity Domain Restructuring](./activity_domain_restructuring.md)
