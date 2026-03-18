# UI System Governance (SaaS Polish)

Purpose: keep `Home`, `Explore`, `Teams`, and `Profile` visually and behaviorally consistent with a modern SaaS standard.

## 1-minute Rule
- Every primary page must answer in the first viewport:
  - Where am I?
  - What is happening?
  - What should I do next?

## Component Rules
- Grid: 12-column layout on desktop for all analytics/discovery pages.
- Card language:
  - one base surface model
  - one hover model
  - consistent border softness + shadow depth
- Button hierarchy:
  - one dominant primary action per section
  - secondary actions visibly quieter
  - avoid two competing primaries in one block
- Section pattern:
  - title
  - helper microcopy
  - card/content

## State Rules
- Every major surface must define:
  - loading state
  - empty state with one clear next action
  - error state with retry path
- Empty-state copy should be instructional, not passive.

## Interaction Rules
- Motion: 120-200ms transitions for list/card/filter updates.
- Hover/focus/disabled states must be present for all interactive controls.
- Icon-only controls require ARIA label + tooltip.

## Data Surface Rules
- Metrics: icon + label + value + context model.
- Charts: always include title + context text.
- Tables:
  - fixed first column rhythm for identity cells
  - aligned numeric columns
  - readable row density

## Typography Rules
- Preserve one shared scale across pages:
  - page title
  - section title
  - card title
  - body/meta
- Avoid local one-off font-size overrides unless documented.

## Audit Checklist (Pass/Fail)
- [ ] Page has clear primary action in first viewport.
- [ ] No section has two equal primaries.
- [ ] Section headers follow title + helper text pattern.
- [ ] Card hover style matches system baseline.
- [ ] Empty states include clear next action.
- [ ] Focus states are visible on keyboard navigation.
- [ ] Icon-only controls have label/tooltip.
- [ ] Chart and table surfaces include context text.
- [ ] Button sizing/spacing matches system baseline.
- [ ] Typography scale matches shared page hierarchy.
