> Historical design reference. The React implementation and current product contract are documented in [React redesign](../../react_redesign_plan.md). NiceGUI-specific implementation instructions are retired.

ith# App Redesign Brief

This document defines the preferred app-wide redesign direction based on what the product actually does today.

The aim is to redesign around the real v1 behavior, not around aspirational modules or page-by-page visual invention.

## Goal

Design the app as a calm internal learning workspace with three primary modes:

- discover useful learning content
- focus on your own next steps
- follow shared team momentum

This should feel like one coherent product, not a set of unrelated dashboards.

## Product Model

The real product is strongest when expressed as:

- share
- discover
- review
- track
- organize with paths
- follow lightweight team activity

The redesign should reinforce that model directly.

## Information Architecture

### Primary Modes

#### 1. Explore

Purpose:
- discover what people are learning
- search and filter the catalog
- open details
- track, review, or share

Mental model:
- library / catalog

This should be the canonical discovery surface.

#### 2. Focus

This is the current `Home` concept, but the redesign should treat it as a personal workspace rather than a dashboard.

Purpose:
- see your next useful action
- continue tracked learning
- follow your selected path
- respond to review/follow-up needs

Mental model:
- personal workspace

Potential naming:
- `Focus`
- `My learning`
- `Workspace`

#### 3. Team

This is the current `Teams` surface.

Purpose:
- follow activity in one or more teams
- see inbox/follow-up items
- manage membership
- move between team context and shared learning details

Mental model:
- shared stream / shared workspace

### Secondary Surfaces

#### Profile

Purpose:
- show personal and team stats

Mental model:
- stats utility surface

#### Admin

Purpose:
- operational user/team management

Mental model:
- admin workspace

## Page Purpose Rules

Every page should have one dominant purpose.

### Explore
- browse and act on content
- do not make it a dashboard

### Focus
- answer “what should I do next?”
- do not make it a stats page

### Team
- answer “what is happening in this team and what needs follow-up?”
- do not make it a settings page

### Profile
- answer “how am I doing / how is the team doing?”
- do not make it a workspace

### Admin
- answer “what admin action do I need to take?”
- do not make it a branded product showcase

## Layout Templates

The app should use a small number of templates.

### Template A: Library

Use for:
- Explore

Shape:
- header
- control bar
- content grid/list

Characteristics:
- strong search and filter controls
- stable content rhythm
- low visual drama

### Template B: Personal Workspace

Use for:
- Focus

Shape:
- header
- main left column
- support right column

Left column:
- next step
- tracked items
- selected path

Right column:
- pending actions
- recent team follow-up
- small team signal

Characteristics:
- operational
- compact
- action-first

### Template C: Shared Workspace

Use for:
- Team

Shape:
- header
- team switcher / workspace nav
- main feed or inbox
- light secondary context panel

Characteristics:
- stream-oriented
- fewer empty-state cards
- one coherent activity language

### Template D: Utility Workspace

Use for:
- Admin
- Profile

Shape:
- header
- compact controls or mode switch
- stable utility cards / tables / charts

Characteristics:
- direct
- calm
- less editorial framing

### Template E: Detail

Use for:
- course/article/video/path detail pages

Shape:
- header / breadcrumb
- main content column
- secondary action rail

Characteristics:
- tight section rhythm
- compact reviews
- actions support the content, not the other way around

## Component System

The redesign should converge on a small set of primitives.

### 1. Content Card

Use for:
- course
- article
- video
- path

Must be:
- stable in height/rhythm
- predictable CTA placement
- minimal metadata variance

### 2. Utility Card

Use for:
- forms
- admin actions
- workspace actions

Must be:
- simple
- low ornament
- easy to scan

### 3. Stats Card

Use for:
- metrics
- grouped counts
- lightweight progress summaries

Must be:
- compact
- not oversized

### 4. Feed/List Row

Use for:
- conversations
- inbox
- activity
- table-like recent items

Must be:
- wider and calmer than current mini-cards
- feel like a list system, not isolated floating cards

### 5. Detail Sidebar Card

Use for:
- actions
- metadata
- secondary context

Must be:
- visually quieter than main content

## Shell Direction

Preferred long-term shell:

- fixed left navigation
- compact top utility bar
- single content canvas

Important:
- this is a design direction, not an immediate migration requirement
- adopt progressively where it improves layout stability

## Naming Recommendations

### Current `Home`

The current name is serviceable, but weak.

Better options:
- `Focus`
- `My learning`
- `Workspace`

Recommendation:
- `My learning` if you want clarity
- `Focus` if you want stronger product identity

### `Teams`

This is acceptable, but the UI should emphasize:
- activity
- follow-up
- team stream

not:
- private content containers

### `Profile`

Keep the name.

### `Explore`

Keep the name.

## Visual Direction

The app should feel:

- calm
- dark
- structured
- product-like
- low-friction

It should not feel:

- overly cinematic
- overframed
- over-instrumented
- like every page is a separate dashboard design experiment

## What To Remove From The Current Direction

- repeated intro/hero layers
- too many special-case cards
- giant empty-state blocks
- decorative section stacks
- pages mixing dashboard, content, and admin language at once

## What To Emphasize

- content and action clarity
- stable layout
- fewer patterns
- stronger page purpose
- consistent rhythm across all primary surfaces

## Recommended Execution Order

1. lock the app-wide page purposes
2. lock the small template set
3. reshape `Focus` / current `Home`
4. reshape `Explore`
5. reshape `Team`
6. align `Profile` and `Admin`
7. standardize detail pages last

## Relationship To Other Docs

- `docs/nicegui_design_baseline.md`
  - stable NiceGUI-native layout rules
- `docs/nicegui_design_implementation_plan.md`
  - phased rollout plan
- this document
  - app-wide product/design direction for the redesign
