# Reviews

## Purpose

Provide lightweight peer feedback on shared learning content and learning paths.

## Functional Design

### User outcome

Users can:

- add or update their review for a course
- add or update their review for an article
- add or update their review for a video
- add or update their review for a path
- view review summaries and review lists

### In scope for v1

- one review per user per target
- rating plus optional text
- summary data for list/detail surfaces
- moderation via creator/admin delete rules where implemented

### Out of scope for v1

- threaded review discussions
- review requests
- reaction systems
- moderation dashboards

### Canonical flows

1. User opens a detail view.
2. User submits rating and optional text.
3. Subsequent submit updates the same review rather than creating a duplicate.
4. Other users see updated summaries and lists.

### Error behavior

- invalid rating: `400`
- missing target: `404`
- unauthorized access: `401`
- forbidden moderation action: `403`

## Technical Design

### Backend contract

- course reviews under `/courses/{id}/reviews`
- article reviews under `/articles/{id}/reviews`
- video reviews under `/videos/{id}/reviews`
- path reviews under `/paths/{id}/reviews`

### Frontend contract

- review actions live on item and path detail surfaces
- summary badges appear on list/detail contexts

### Data model

- `course_reviews`
- `article_reviews`
- `video_reviews`
- `path_reviews`

### Release constraints

- Reviews are part of v1 for all four target types.
- The product should avoid implying recommendations or tracking support where only reviews exist.
