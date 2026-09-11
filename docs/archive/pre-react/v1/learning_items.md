# Learning Items

## Purpose

Make courses, articles, and videos first-class learning items that users can share and browse in one product.

## Functional Design

### User outcome

Users can:

- share a course
- share an article
- share a video
- browse all shared items in Explore
- open item detail views

### In scope for v1

- canonical share route for a single item
- item subtypes:
  - `course`
  - `article`
  - `video`
- explore listing and detail routes
- item ownership via `created_by`

### Capability model

- `course`: tracking and reviews
- `article`: reviews only
- `video`: reviews only

This asymmetry is part of the v1 design. V1 should not imply that all item types support the same actions.

### Out of scope for v1

- audience-scoped sharing
- rich media ingestion pipeline
- durable metadata persistence
- recommendation flows
- tracking for videos

### Canonical flows

1. User opens `/share/item?type=course|article|video`.
2. User submits a valid share form.
3. Item appears in Explore and detail views.
4. Other users can open, review, or track the item depending on subtype rules.

### Error behavior

- missing required fields: `400`
- duplicate URLs or duplicate title/provider combinations where enforced: `409`
- unauthorized access: `401`

## Technical Design

### Backend contract

- `/courses`
- `/articles`
- `/videos`

Each subtype keeps its own API family and persistence model.

### Frontend contract

- `/share/item`
- `/explore`
- `/explore/courses/{course_id}`
- `/explore/articles/{article_id}`
- `/explore/videos/{video_id}`

### Data model

- `courses`
- `articles`
- `videos`

### Release constraints

- The README and UI copy must present the subtype capability model accurately.
- Metadata suggestion/import is optional support behavior, not part of the core v1 promise.
- If URL preview metadata is not hardened, that feature should be disabled rather than treated as required v1 behavior.
