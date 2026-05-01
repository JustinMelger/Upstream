# Frontend Target Shape

This document defines the preferred structure for main NiceGUI feature areas after v1.

It is a target shape, not a retroactive requirement that every existing page already meets.

## Goal

Make page packages consistent enough that contributors can predict where code belongs.

## Package Shape

For a typical page area, prefer this structure:

- `page.py`
  - route registration
  - top-level page assembly
  - light composition only
- `controller.py`
  - async workflows
  - mutation orchestration
  - backend/service coordination
- `view_model.py`
  - payload shaping for UI
  - card/detail row mapping
  - display-oriented derived fields
- `reducers.py`
  - filter/sort/derive helpers
  - deterministic transformations from state to shown rows
- `sections.py`
  - reusable render blocks for that page
  - no direct API calls
- `actions.py`
  - reusable UI action callbacks when multiple sections/cards share the same action logic
- `dialogs.py`
  - dialog construction and dialog-local event wiring
- `state.py`
  - typed page state containers only
- `ui_glue.py`
  - lightweight formatting or page-local helper functions when they do not belong in core/services
- `components/*`
  - reusable primitives shared across multiple page areas

## Boundary Rules

### `page.py`

Allowed:
- route registration
- composing sections
- creating page-scoped controller/state objects
- wiring top-level refresh callbacks

Avoid:
- direct API calls
- mutation-heavy business workflows
- large inline render trees when a section helper would make ownership clearer

### `controller.py`

Allowed:
- API/service coordination
- mutation sequencing
- refresh/reload orchestration
- canonical action flows shared within the page area

Avoid:
- importing `nicegui.ui`
- rendering concerns
- page-specific styling decisions

### `view_model.py` and `reducers.py`

Allowed:
- deterministic transforms
- formatting for display
- sorting/filtering/selection derivation

Avoid:
- side effects
- API calls
- hidden mutation of shared page state

### `sections.py`

Allowed:
- rendering cards, rails, empty states, summaries, and structured page blocks
- accepting already-derived data and callback dependencies

Avoid:
- direct transport calls
- hidden page orchestration
- broad callback bundles with many unused members

## Preferred Mutation Pattern

When a user triggers a mutation:

1. render layer calls a controller/action callback
2. controller performs API work
3. controller updates or reloads the minimum required state
4. render layer is refreshed
5. user receives feedback

Prefer targeted refreshes over reloading the entire page.

## Preferred Navigation Pattern

- navigation targets should be canonical and consistent across surfaces
- detail pages should return users to the matching Explore tab or source context where appropriate
- the same item type should not navigate differently depending on which page triggered the action unless the difference is intentional

## Shared Surface Expectations

### Explore
- canonical discovery surface
- detail routes are the canonical item/path deep links

### Home
- personal next-step dashboard
- should favor operational summaries and next actions over explanatory chrome

### Teams
- group activity and follow-up workspace
- should not imply private catalog visibility in v1

### Profile
- stats and progress surface
- should stay analytical and direct

## Smells That Usually Mean Refactor

- render functions that call APIs directly
- helper functions that accept many unused callbacks or state objects
- page files that own sorting/filtering/mutation logic directly
- the same mutation-refresh sequence repeated across multiple surfaces
- UI code needing to understand backend payload quirks in multiple places

## Adoption Order

Use this shape first when touching:

1. Teams
2. Profile
3. Home
4. detail pages
5. any older section-heavy page package

Do not force full package reshapes unless the area is already being changed for a real reason.
