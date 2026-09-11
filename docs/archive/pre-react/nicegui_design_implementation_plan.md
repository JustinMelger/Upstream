> Historical design reference. The React implementation and current product contract are documented in [React redesign](../../react_redesign_plan.md). NiceGUI-specific implementation instructions are retired.

# NiceGUI Design Implementation Plan

This plan turns `docs/nicegui_design_baseline.md` into a practical rollout sequence.

The goal is to simplify the frontend layout system without turning the work into a broad redesign project or a product-scope expansion.

## Goal

Move the NiceGUI frontend toward a more stable layout system by:

- reducing layout variation
- reducing card variation
- making page rhythm more predictable
- fixing layout shift caused by data-dependent page structures

This is a UI-system implementation plan, not a feature roadmap.

## Working Constraints

- keep the shipped v1 product model intact
- do not introduce recommendation-heavy or merchandising-heavy modules from the mockups
- prefer layout simplification over visual experimentation
- avoid broad shell rewrites unless they clearly improve stability
- remove obsolete layout variants as pages migrate

## Phase A: Baseline Primitives

Goal:
- define the shared layout primitives before reshaping individual pages

Work:
- define the preferred page shells:
  - `header -> controls -> main content`
  - `header -> summary row -> main content`
  - `header -> primary content + secondary sidebar`
- define the core card roles:
  - content card
  - stats card
  - utility/action card
  - detail/sidebar card
- normalize shared spacing, padding, section rhythm, and max-width behavior
- reduce fragile one-off grid behavior where possible

Deliverables:
- shared theme/layout class updates in `frontend/ui/nicegui/core/theme.py`
- a short note in `docs/nicegui_design_baseline.md` if any baseline rule changes during implementation

Exit criteria:
- shared primitives exist
- no page-specific migration has to invent new layout patterns just to proceed

## Phase B: Highest-Risk Page Migrations

Goal:
- stabilize the pages most affected by layout shift and over-composition

Priority order:

1. `Home`
2. `Explore`
3. `Teams`

### Home

Focus:
- reduce layout shifts from tracked courses / selected paths / team activity changes
- prefer one primary block and stable companion blocks
- remove grid/span behavior that causes major reflow when content appears

Success condition:
- adding or removing tracked content does not make the page feel structurally different

### Explore

Focus:
- keep one compact search/filter/share shell
- simplify section framing
- make sparse states look intentional

Success condition:
- the page works as one stable discovery surface rather than several stacked layout modes

### Teams

Focus:
- keep one workspace shell
- reduce repeated empty-state framing
- make inbox/activity feel like one cohesive surface

Success condition:
- empty and populated states feel like the same page, not different compositions

## Phase C: Natural-Fit Page Migrations

Goal:
- apply the same baseline to pages that should benefit with lower risk

Priority order:

1. `Admin`
2. `Profile`
3. detail pages

### Admin

Focus:
- utility/action card consistency
- stable two-column dashboard-like form layout

### Profile

Focus:
- stats-first layout
- stable summary rail and analytics sections

### Detail Pages

Focus:
- one clear detail template:
  - header/breadcrumb
  - main content
  - secondary action rail
- compact review sections
- consistent sidebar strength

## Phase D: Cleanup And Consolidation

Goal:
- remove the old layout system residue once the new baseline is in use

Work:
- remove obsolete page-local layout classes
- remove duplicate card variants that are no longer needed
- remove unused spacing and grid rules from `theme.py`
- update docs if the implementation refines the original baseline

Exit criteria:
- migrated pages use the new baseline consistently
- old layout forks are reduced instead of preserved indefinitely

## Execution Rules

For each phase:

- keep changes page-scoped where possible
- do not mix unrelated feature work into the same change
- verify layout changes with focused tests where behavior changes
- prefer deleting fragile layout rules over layering new exceptions on top
- if a page needs many exceptions, simplify the page structure instead

## Recommended First Implementation Slice

Start with:

1. `Phase A`
2. `Home` from `Phase B`

Reason:
- Home has the clearest layout-shift problem today
- it will pressure-test whether the baseline is actually simpler
- it will likely inform how Explore and Teams should be simplified next
