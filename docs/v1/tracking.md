# Tracking

## Purpose

Allow users to track their course progress and selected-path progress in a simple, explicit way.

## Functional Design

### User outcome

Users can:

- set course status
- view their own tracked learning state
- select paths into their learning workspace
- update selected-path status

Admins can:

- view broader tracking stats and team-level aggregate tracking endpoints

### In scope for v1

- course statuses:
  - `interested`
  - `in_progress`
  - `completed`
- selected path management
- path progress/status on user-selected paths
- user and admin tracking stats already present in the API

### Out of scope for v1

- video tracking
- article tracking
- advanced analytics or recommendation loops

### Canonical flows

1. User marks a course status.
2. User sees that state reflected in course and learning views.
3. User selects a path.
4. User updates the selected path’s status.

### Error behavior

- invalid status: `400`
- unauthorized access: `401`
- admin-only aggregate access: `403`

## Technical Design

### Backend contract

- `/tracking`
- `/tracking/stats`
- `/tracking/stats/users`
- selected-path behavior under `/paths` and `user_paths`

### Frontend contract

- course tracking appears on course-related surfaces
- learning/home/profile surfaces reflect tracked state and selected paths

### Data model

- `tracking`
- `user_paths`

### Release constraints

- Tracking scope must stay narrow and honest: courses and path progress only.
- Any UI copy suggesting “track all learning items” should be removed for v1.
