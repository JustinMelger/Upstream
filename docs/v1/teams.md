# Teams

## Purpose

Provide a basic workspace for grouping users and viewing team-relevant activity around shared learning.

## Functional Design

### User outcome

Users can:

- create a team
- view teams they belong to
- open team detail
- see team member lists
- see inbox activity
- see team activity

Owners and admins can:

- add members
- update member roles where supported
- remove members, subject to owner protections

### In scope for v1

- team creation
- membership management
- basic team detail
- inbox and activity follow-up around shared learning
- team activity feed
- inbox/team activity tabs in the `/teams` surface
- globally visible Explore catalog with team activity as a relevance lens

### Out of scope for v1

- audience-scoped sharing
- team-private catalog visibility
- team invitations
- review request workflows
- discussions or conversations
- advanced collaboration permissions

### Canonical flows

1. User creates a team.
2. Owner adds members.
3. Shared learning remains discoverable in Explore for authenticated users.
4. Member opens the team workspace to follow inbox updates and team activity.
5. Team activity reflects member-generated events and shared-learning momentum.

### Error behavior

- non-member team access: `403`
- missing team: `404`
- non-manager membership mutation: `403`
- invalid role or owner-removal attempts: `400`

## Technical Design

### Backend contract

- `POST /teams`
- `GET /teams/mine`
- `GET /teams/{team_id}`
- `POST /teams/{team_id}/members`
- `DELETE /teams/{team_id}/members/{user_id}`
- `GET /teams/{team_id}/activity`

### Frontend contract

- `/teams`
- one page is the canonical team workspace route
- Explore remains the canonical discovery/catalog route

### Data model

- `teams`
- `team_members`
- team activity is derived from other content/share/review events

### Visibility model

- Explore is global for authenticated users in v1.
- Team association is a relevance/activity context, not an access-control boundary.
- Joining a team gives users better follow-up context through Inbox and team activity; it does not unlock hidden catalog items.

### Release constraints

- Teams should be presented as a basic workspace feature, not a full collaboration platform.
- Teams should not be described as private content spaces in v1.
- Dead or duplicate `/teams` page implementations in the frontend should be removed or clearly marked non-canonical.
