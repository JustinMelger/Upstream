> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# React redesign implementation record

The React release implements the documented calm dark workspace with **My learning**, **Explore**, **Activity**, and **Share**. FastAPI/PostgreSQL remain the backend and source of truth. This document supersedes the earlier provisional migration plan.

## Delivered scope

- React/TypeScript/Vite, declarative React Router, TanStack Query, Radix interaction primitives, CSS Modules, and local font assets.
- Responsive sidebar/drawer, shared forms/cards/dialogs, loading/empty/error states, and safe internal/external navigation.
- Personal next action, tracked courses, selected paths, contributions, paginated discovery, subtype details/reviews, sharing/editing/deletion, personal stats/activity, Profile, and Admin.
- Optional author recommendation notes on all four content types; articles/videos now support owner/admin editing and deletion.
- Browser cookie authentication, session-bound CSRF, origin checks, header precedence, expiry/disabled-user checks, current-session logout, and reset revocation.
- SQL-backed bounded catalog, personal collection, summary, path-progress, and activity APIs with generated OpenAPI TypeScript contracts.
- Static React/Nginx deployment alongside the Python API; updated Docker/Compose, local commands, and CI.
- Teams and AI routes retired. Old Teams/profile-stat links redirect. NiceGUI source/runtime/tests removed in favor of React tests.

## Explicit product decisions

Course tracking remains unchanged. Article/video completion is deferred. Path progress says “X of Y courses completed”; zero-course paths have no percentage, and manual status is independent.

Activity has For you and Shared activity scopes, plus personal current totals. It contains content shares and reviews, never other users' private course progress. No team membership, leaderboards, streaks, or invented historical charts.

Notes are nullable plain text up to 1,000 characters. Omitted update notes are preserved; explicit null clears them. Content deletion removes associated reviews/path references but retains the path, including an empty path.

Explicit metadata autofill is available for new courses, articles, and videos; see [implementation and safeguards](metadata_autofill_implementation.md). Manual forms remain complete and external preview-image fetching stays disabled. Historical paths without dates do not appear as newly shared merely because of migration.

## Delivery and validation

The release gates are backend regression/security/privacy/migration tests; frontend lint/types/unit/build; OpenAPI drift; and real-browser workflows for discovery/tracking, sharing/editing/reviews, mixed paths, Admin, and 390/768/1440px layouts. Use only disposable test databases: fixtures truncate tables and demo seeding refuses ordinary databases.

Verified locally on 2026-09-09:

| Gate | Evidence |
|---|---|
| Backend | 164 passing PostgreSQL regression tests, including CSRF/header precedence, production cookies, session revocation, ownership, notes, privacy, stable pagination, and bounded query counts |
| Frontend | 12 passing unit/component tests; ESLint, TypeScript, Prettier, and Vite production build pass |
| Browser | 10 passing scenarios against real FastAPI/PostgreSQL, including all item types, reviews, mixed paths, keyboard ordering, Admin, retained drafts after errors, and three viewport widths |
| Visuals | 14 reviewed Linux Chromium baselines and passing comparisons for primary screens plus empty/loading/error states at 390px and 1440px |
| Migration | Fresh migration chain and populated legacy upgrade preserve every original field across 14 tables, including reviews, tracking, selections, IDs, authors, and Teams rollback data |
| Deployment | API and Nginx images build; same-origin login/CSRF/logout, API docs, SPA deep links, and JSON API errors verified through Docker on localhost |
| Contracts/quality | OpenAPI export/type generation, Ruff, mypy, and import boundaries pass; npm and Python dependency audits report no known vulnerabilities |

These are local checks; hosted CI will run on the next push/PR. The repository includes separate API/UI image publishing and a visual-regression job that fails on unreviewed differences.

See the README for exact setup and test commands. The `scripts/seed_react_demo.py` dataset is test-only and never runs during production startup.

## Cutover and delayed cleanup

The repository contains the new deployment configuration; actual production cutover requires the operator's target host, TLS ingress, and secrets. Keep the previous NiceGUI image and header authentication available for one release cycle. Reauthentication in React is expected.

Team tables and historical Alembic migrations are deliberately retained. Dropping those tables is delayed until the rollback window closes and a recoverable backup exists. No destructive team-data migration is included in this release.

## Remaining follow-up

Universal article/video completion, generated summaries, historical event analytics, and eventual team-table removal are separate releases. Existing deployment environments must explicitly set production origins and secrets before switching traffic.

## Frontend UX refinement

The follow-up [UX refinement release](frontend_ux_refinement.md) adds a warmer semantic palette, compact learning guidance, inline status controls, searchable facets, mobile filters, feed-first Activity views, improved review/form interactions, and browser-session draft recovery. Personal selected-path totals are exposed only through the learning read model. It requires no schema migration. The original verification table above records the initial redesign; see the refinement record for subsequent verification.
