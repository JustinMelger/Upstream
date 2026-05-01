# Stable NiceGUI Design Baseline

This document defines the preferred post-v1 UI direction for the NiceGUI frontend.

The goal is not to make the product look more “designed” in the abstract. The goal is to make the UI more stable, more maintainable, and more native to NiceGUI.

This baseline is intentionally simpler than some of the current pages and narrower than the richer mock concepts.

## Goal

Move the frontend toward:

- more stable page rhythm
- fewer layout shifts as data appears or disappears
- fewer custom layout variants
- fewer one-off card patterns
- a calmer, more predictable NiceGUI-native structure

The baseline should favor structural stability over visual flourish.

## Core Principle

Use the mockups as a layout-system reference, not as a product-scope expansion.

Keep:
- the calmer shell
- the fixed navigation idea
- the more regular card/grid rhythm
- the simpler control bars

Do not automatically import:
- recommendation-heavy modules
- richer merchandising sections
- denser enterprise-dashboard content blocks that do not match the shipped v1 product

## Design Rules

### 1. Prefer Stable Page Skeletons

For main surfaces, prefer one of these page shapes:

- `header -> controls -> main content`
- `header -> summary row -> main content`
- `header -> primary content + secondary sidebar`

Avoid:
- hero + utility strip + summary strip + grid + sub-grid stacks on the same page
- multiple stacked intro panels explaining the same thing
- section compositions that change drastically when one item appears

### 2. Reduce Layout Modes

Prefer:
- one-column content pages
- stable two-column pages
- predictable dashboard rows

Avoid:
- mixing custom 12-column spans, ad hoc asymmetry, and per-page grid logic unless clearly necessary
- surfaces that depend on multiple conditional grid templates

### 3. Use Fewer Card Types

The frontend should converge on four main card roles:

- content card
  - learning item or path summary
- stats card
  - one metric or grouped metric summary
- utility/action card
  - forms, admin actions, focused controls
- detail/sidebar card
  - metadata, actions, secondary context

Avoid creating new card families when an existing role can be reused with lighter content variation.

### 4. Favor Fixed Internal Rhythm

Cards should have:

- stable padding
- stable title/subtitle spacing
- predictable CTA position
- minimum heights only where they truly improve rhythm

Avoid:
- cards that stretch dramatically based on one optional field
- cards whose CTA row shifts far up/down depending on content length
- oversized empty states that dominate the page

### 5. Let NiceGUI Stay NiceGUI

This frontend should behave like a disciplined NiceGUI app, not like a custom React design system forced through NiceGUI primitives.

Prefer:

- clear rows and columns
- stable cards
- tabs
- tables
- simple control bars
- direct visual hierarchy

Avoid:

- too many layered wrappers
- cinematic page compositions
- layout tricks that only work when the data is ideal

## Page Templates

### Dashboard / Home

Preferred shape:

- page header
- compact mode toggle or action row
- one primary “next step” block
- one stable secondary row
- one tertiary section for conversations/activity

Rules:

- keep the first screen short
- do not stack multiple explanatory panels
- use one clear primary block and a few stable companion blocks
- empty states should compress, not expand

### Explore

Preferred shape:

- page header
- one compact search/filter/share bar
- one featured or spotlight area at most
- one stable content grid/list area

Rules:

- no oversized hero
- controls should read as one system
- sparse result states must still look intentional
- favor consistent list/grid patterns over many special sections

### Teams

Preferred shape:

- page header
- one action strip
- one workspace body

Empty state:

- one primary CTA block
- one guidance block
- no repeated explanatory cards

Rules:

- Teams should feel like a workspace, not a settings page
- Inbox and activity should share one rendering language

### Profile

Preferred shape:

- page header
- mode switch (`My stats` / `Team totals`)
- compact summary rail
- stats content

Rules:

- analytical and direct
- no repeated “overview” wrappers
- charts/tables should feel like one coherent stats surface

### Admin

Preferred shape:

- page header
- stable two-column utility-card layout
- one table/list section

Rules:

- this is the best fit for the calmer dashboard style
- utility forms should share one common card pattern

### Detail Pages

Preferred shape:

- page header/breadcrumb
- main detail column
- secondary action rail

Rules:

- content sections should be tighter than dashboard sections
- review areas should be compact and repeatable across types
- the sidebar should support the content, not overpower it

## Navigation Baseline

Preferred shell direction:

- stable left navigation for main areas
- compact top utility area
- one content canvas with predictable max width

Important:

- this is a layout-system direction, not a requirement to immediately rebuild the app shell
- adopt it progressively where it improves stability and does not force major routing churn

## First Reshape Targets

These are the best candidates for moving toward this baseline first:

1. `Home`
   - biggest layout-shift risk
   - most sensitive to data-dependent resizing

2. `Explore`
   - should move to one more stable search/filter/content rhythm

3. `Teams`
   - should become a calmer workspace shell

4. `Admin`
   - strongest natural fit for the mock direction

5. `Profile`
   - already improved; mostly keep tightening toward the same system

## Working Rules For Adoption

When reshaping a page toward this baseline:

- do not expand product scope just because the mock supports it
- prefer removing sections over inventing new ones
- choose stable layout over clever density
- keep page structure predictable across data states
- if a page needs many layout exceptions, simplify the page instead of adding more CSS

## Relationship To Other Docs

- `docs/frontend_target_shape.md`
  - defines code/package structure
- `docs/architecture_standards.md`
  - defines engineering rules
- this document
  - defines the preferred visual/layout system for NiceGUI pages
