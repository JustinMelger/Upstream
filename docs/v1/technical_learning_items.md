# Technical Design: Learning Items

## Goal

Describe how the current codebase models and serves the three learning-item types kept in v1.

## Canonical Model

Learning Hub v1 has three first-class learning-item subtypes:

- course
- article
- video

They share product intent, but they do not share identical capabilities.

## Backend Shape

- courses:
  - router: `backend/api/courses.py`
  - service: `backend/services/courses_service.py`
  - repository: `backend/database/async_repositories/courses.py`
- articles:
  - router: `backend/api/articles.py`
  - service: `backend/services/articles_service.py`
  - repository: `backend/database/async_repositories/articles.py`
- videos:
  - router: `backend/api/videos.py`
  - service: `backend/services/videos_service.py`
  - repository: `backend/database/async_repositories/videos.py`

## Frontend Shape

- explore routes:
  - `/explore`
  - `/explore/courses/{id}`
  - `/explore/articles/{id}`
  - `/explore/videos/{id}`
- share route:
  - `/share/item?type=course|article|video`

The canonical single-item share UI is centralized under `/share/item`.

## Capability Matrix

| Type | Share | Browse | Detail | Review | Tracking | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| course | yes | yes | yes | yes | yes | no for v1 |
| article | yes | yes | yes | yes | no | no |
| video | yes | yes | yes | yes | no | no |

## Data Model

- `courses`
- `articles`
- `videos`
- review tables by subtype
- tracking tables for course/path only

## Accepted V1 Constraints

- no attempt to unify all subtype behaviors behind an artificial shared mutation model
- tracking remains course/path specific
- URL metadata/autofill is optional support behavior, not a core product promise

## Release Risks

- docs and UI copy may overstate symmetry across item types
- metadata/autofill can be mistaken for core item persistence behavior
- video support should be presented as lightweight but valid, not as an unfinished course variant

## Out Of Scope

- all recommendation flows in the released v1 product
- article/video tracking
- richer media ingestion or durable source metadata model
