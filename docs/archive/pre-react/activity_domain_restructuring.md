> Historical NiceGUI-era guidance, superseded by the [React implementation record](../../react_redesign_plan.md) and current [frontend architecture](../../architecture_frontend.md).

# Activity Domain Restructuring

This document defines what a future activity-domain restructuring would mean for Learning Hub after Phase 1 cleanup.

It is not a Phase 1 task and not a release blocker. The goal is to make the activity-related parts of the product feel like one intentional subsystem instead of several adjacent surfaces that evolved separately.

## Why This Exists

The v1 product now has a clearer activity model than it did during development, but the implementation still reflects its history:

- Teams inbox
- team activity feed
- Home conversations / recently shared items
- Profile team stats
- notifications/activity backend feed

These surfaces work, but they are not yet driven by one clean activity domain model.

## Current Problems

### 1. Activity And Inbox Are Too Close Conceptually

The product distinguishes:

- `activity`: what happened
- `inbox`: what needs my attention

But in the code they are still modeled as very similar feed variants.

Impact:

- weaker mental model for contributors
- copy and naming drift across Home, Teams, and backend feed logic
- higher risk of subtle UX inconsistency when one surface changes

### 2. Surfaces Still Own Slightly Different Shapes Of “The Same Thing”

Today:

- Teams renders activity feed rows
- Home renders “conversations needing you” and “recently shared” summaries
- Profile renders team stats only
- backend notifications expose a lightweight feed

Those are related, but they are not clearly layered.

Impact:

- repeated shaping logic
- unclear responsibility boundaries
- harder future changes when a new event type is added

### 3. UI-Shaped Rows Leak Too Early

Some of the current logic still effectively says:

- “build rows for this page”

instead of:

- “produce canonical domain events, then project them for each surface”

Impact:

- UI behavior is easier to ship quickly
- domain behavior is harder to evolve consistently

### 4. Terms Are Not Yet Strict Product Concepts

These terms now exist in the app:

- activity
- inbox
- conversations
- updates
- follow-up
- team stats

They are better aligned than before, but they are not yet strict domain terms with one clear ownership map.

## Target Product Model

The target model should be:

- `Explore`
  - global discovery surface
  - not an activity feed
- `Home`
  - personal next-step dashboard
  - consumes inbox/follow-up signals and lightweight team momentum summaries
- `Teams`
  - group follow-up and activity workspace
  - owns inbox and team activity feed presentation
- `Profile`
  - personal and team stats
  - does not own activity feed behavior

## Target Domain Model

### 1. Canonical Activity Event

Introduce one explicit activity event model that backend services produce before UI projection.

Suggested fields:

- `event_type`
- `actor`
- `happened_at`
- `target_type`
- `target_id`
- `target_label`
- `team_id` or `team_context`
- `requires_follow_up`
- `follows_up_for`

This should be domain-shaped, not page-shaped.

### 2. Canonical Event Types

The exact list can evolve, but it should be deliberate and finite.

Candidate v2 event types:

- `share_created`
- `review_created`
- `review_deleted`
- `path_selected`
- `tracking_started`
- `tracking_completed`

Not every UI needs every event type, but they should all come from one vocabulary.

### 3. Inbox As A Projection, Not A Sibling Feed

The target rule should be:

- activity = all relevant events for a scope
- inbox = filtered subset of activity where `requires_follow_up = true`

That keeps one event pipeline while allowing different UI surfaces.

### 4. Team Stats Are Separate From The Event Feed

Profile should consume:

- stats aggregates

not feed rows.

That means:

- Home and Teams may depend on event-derived signals
- Profile should depend on stats-specific services and projections

## Target Ownership Boundaries

### Backend

- repositories return raw persisted activity/stat source rows
- services map those rows into:
  - canonical activity events
  - canonical inbox projections
  - canonical stats aggregates

### Frontend

- `shared_activity/*`
  - feed projection helpers only
- `teams/*`
  - owns inbox and team activity workspace composition
- `learning/*`
  - owns personal next-step projections and lightweight activity summaries
- `profile/*`
  - owns stats presentation only

## Migration Plan

This should happen in stages, not in one rewrite.

### Stage 1: Contract Definition

Deliverables:

- define canonical activity event fields
- define inbox projection semantics
- define approved event types
- document ownership map across Home, Teams, Profile, backend notifications

No UI rewrite required yet.

### Stage 2: Backend Event Shaping

Deliverables:

- build one backend service-layer event mapping contract
- keep existing endpoints, but have them project from the same event model
- reduce page-specific shaping logic in repositories/services

Success criteria:

- adding a new event type happens in one main event-mapping layer

### Stage 3: Frontend Projection Cleanup

Deliverables:

- `shared_activity/*` consumes canonical event rows
- Teams inbox and team feed become explicit projections over the same event model
- Home consumes summarized follow-up and activity signals rather than bespoke row shapes

Success criteria:

- Teams/Home no longer drift when event logic changes

### Stage 4: Copy And UX Alignment

Deliverables:

- one clear meaning for:
  - activity
  - inbox
  - conversations
  - follow-up
- remove any residual mixed terminology in UI copy and docs

Success criteria:

- contributors and users can describe the subsystem consistently

## Explicit Non-Goals

This restructuring should not automatically include:

- private team-only visibility
- a messaging or chat system
- a notification delivery platform
- a major Explore/Teams product-model change
- a full event-sourcing rewrite

## When To Do This

This is appropriate when at least one of these becomes true:

- adding new activity types starts causing repeated cross-surface changes
- inbox/activity semantics become a recurring source of bugs or confusion
- Home and Teams begin to diverge again in follow-up behavior
- contributors are repeatedly unsure where activity logic belongs

## Practical Outcome

If done well, this restructuring should produce:

- one clearer event vocabulary
- less duplicated feed logic
- stronger Home/Teams/Profile boundaries
- lower contributor confusion
- a safer base for future team/activity features
