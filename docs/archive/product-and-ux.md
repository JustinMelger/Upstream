# Product and UX decisions

Historical summary of the React, UX refinement, visual discovery, supporting pages and course journey records. They were catalogued on 2026-09-11; only the original React validation explicitly states 2026-09-09. Current behaviour is documented in the [product guide](../product.md).

## Learning and privacy

Course-only tracking and independent manual path status were retained through the redesign. Mixed paths count completed courses without implying article/video completion. Shared activity projects content shares and reviews, while personal progress remains private. Earlier proposals for immutable activity history, team feeds and inbox orchestration were not adopted as current functionality.

## Navigation and forms

The UX refinement introduced URL-backed search/filter/page state, staged mobile filters, local mutation errors and versioned session drafts. Draft restoration asks before replacing form values; expiry and explicit logout have different retention rules. These decisions preserve input without storing credentials or creating server-side drafts.

Visual discovery replaced the sidebar presentation with a horizontal header and mobile drawers. A spotlight reuses one result from the first catalog page rather than adding an extra query or duplicate card. Supporting pages reused content projections for attributed excerpts, reviews, profile contributions and account management.

The course journey follow-up separated sharing from tracking, made course addition explicit and added contextual progress feedback, Undo and blocked-popup recovery. Existing tracking APIs were reused; opening a completed course does not reset it. No historical analytics or universal completion model was added.

## Historical validation

The records reported 21 frontend tests/16 browser workflows for UX refinement, 26/18 for visual discovery and 32/30 for the course journey. These were milestone-specific local results. Current checks and screenshots must be run using [operations guidance](../operations.md#tests-and-quality-checks).
