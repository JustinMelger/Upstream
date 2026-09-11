> Historical NiceGUI-era guidance, superseded by the [React implementation record](../../react_redesign_plan.md) and current [frontend architecture](../../architecture_frontend.md).

# Post-Phase-1 Backlog

This document holds the deferred cleanup and refactor work that stays out of Phase 1.

Phase 1 is complete. The items here are longer-horizon improvements that should be taken on deliberately, not mixed into routine stabilization work.

## Purpose

Use this backlog for:

- structural cleanup that is real but not urgent
- subsystem reshapes that need design work first
- typed-boundary improvements in older areas
- refactors that are only worth doing when the maintenance pain is proven

## P2 Deferred Cleanup And Refactor Work

### 1. Deeper Controller / Service Reshapes

- [ ] Reduce remaining controller methods that still mix transport concerns and page-specific refresh behavior
- [ ] Move repeated mutation-completion logic into clearer controller/service contracts where repetition is now proven
- [ ] Prefer the target page shape in `docs/frontend_target_shape.md` when touching older packages

When to do this:
- after repeated maintenance pain appears in the same page area
- when a feature change would otherwise deepen orchestration drift

### 2. Shared Detail-Page Architecture Extraction

- [ ] Identify the truly repeated parts of course/article/video/path detail pages
- [ ] Extract only stable shared patterns:
  - review summary block
  - sidebar action group
  - detail metadata sections
  - common breadcrumb / return context wiring
- [ ] Avoid generic abstractions unless the shared contract stays easier to read than the current per-page code

When to do this:
- only if repeated changes across detail pages become expensive or error-prone

### 3. Major Activity-Domain Restructuring

- [ ] Use `docs/activity_domain_restructuring.md` as the design baseline
- [ ] Define one canonical activity-event contract
- [ ] Define inbox as a projection over activity, not a sibling subsystem
- [ ] Separate feed projections from stats aggregates across Teams, Home, and Profile

When to do this:
- as a dedicated follow-up project, not as incidental cleanup

### 4. Typed Model Expansion Across Older `dict[str, Any]` Boundaries

- [ ] Identify older controller/service/view-model boundaries that still pass loose dictionaries
- [ ] Introduce typed models first in the highest-churn areas
- [ ] Prefer typed payloads for:
  - activity events
  - detail bundles
  - share form submission payloads
  - profile/team stats projections

When to do this:
- alongside meaningful changes in the affected area, starting with the most frequently touched paths

### 5. Large Test Refactors Purely For Style

- [ ] Keep this explicitly deferred unless a real maintenance problem appears
- [ ] Do not churn tests just to make naming or structure look nicer
- [ ] Only refactor tests broadly when it materially improves signal, speed, or reliability

When to do this:
- only when test maintenance cost becomes a concrete problem

## Working Rule

For backlog items in this document:

- do not mix them casually into small bug-fix changes
- prefer design notes first when the work crosses multiple packages
- keep the product behavior stable unless the change is intentionally broader than cleanup
