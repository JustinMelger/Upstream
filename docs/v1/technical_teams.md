# Technical Design: Teams And Activity

## Goal

Define the narrow team model that is acceptable for v1.

## Canonical Product Meaning

In v1, a team is a lightweight membership container plus a team-scoped activity view.

It is not yet a full audience-sharing, review-request, or discussion system.

## Backend Shape

- router: `backend/api/teams.py`
- service: `backend/services/teams_service.py`
- repository: `backend/database/async_repositories/teams.py`

Core endpoints:

- `POST /teams`
- `GET /teams/mine`
- `GET /teams/{team_id}`
- `POST /teams/{team_id}/members`
- `DELETE /teams/{team_id}/members/{user_id}`
- `GET /teams/{team_id}/activity`

## Frontend Shape

- canonical route: `/teams`
- canonical implementation: `frontend/ui/nicegui/pages/teams/*`

The older `frontend/ui/nicegui/pages/activity/*` package should not be treated as the shipped route implementation if it is not the one registered by the app.

## Data Model

- `teams`
- `team_members`

Activity is assembled from existing share/review events rather than stored as a dedicated team-activity entity.

## Permission Model

- any authenticated user can create a team
- team members can view team detail and team activity
- site admins can bypass some membership restrictions
- team owners/admins can manage members

## Accepted V1 Constraints

- no invitation system
- no scoped sharing audience model
- no conversations/discussions
- no review-request loop

## Release Risks

- teams can be over-positioned as a broader collaboration product than the code actually supports
- duplicate route/page implementations can blur the canonical behavior
- future roadmap items can leak into user-facing docs

## Out Of Scope

- selected-team visibility controls
- review requests
- discussions
- extended collaboration model
