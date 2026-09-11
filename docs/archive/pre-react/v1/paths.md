# Paths

## Purpose

Let users group learning items into ordered learning paths that can be shared and followed.

## Functional Design

### User outcome

Users can:

- create a path
- edit or delete a path they own
- include mixed item types in one path
- browse path detail
- select a path into their learning workflow
- update path progress/status

### In scope for v1

- mixed-item paths with ordered entries
- path share flow
- path detail route
- path selection and path status

### Out of scope for v1

- collaborative path editing
- team-scoped path visibility rules
- advanced workflow automation around paths

### Canonical flows

1. User opens `/share/path`.
2. User creates a path from ordered `course|article|video` items.
3. Path appears in Explore.
4. Another user opens the path and selects it.
5. Selected-path status is updated from learning surfaces.

### Error behavior

- invalid path payload: `400`
- missing path: `404`
- non-owner/non-admin edit or delete: `403`

## Technical Design

### Backend contract

- `/paths`
- `/paths/{id}`
- path item mutation contract uses ordered typed items

### Frontend contract

- `/share/path`
- `/explore/paths/{path_id}`

### Data model

- `paths`
- `path_items`
- `user_paths`

### Release constraints

- Mixed-item paths are part of the v1 contract and must remain explicit in docs.
- Path behavior should stay simple: create, view, select, update status.
- Any broader collaboration semantics around paths are post-v1.
