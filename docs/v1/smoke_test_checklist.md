# V1 Smoke Test Checklist

Use this checklist for a fast release-candidate pass. It is intentionally small and covers the highest-value user paths.

## Preconditions

- Backend is running and migrations are applied.
- Frontend is running.
- At least one admin user can log in.
- Release defaults are active:
  - `FEATURE_AI_CURATOR=0`
  - `FEATURE_TELEMETRY=0`
  - `OTEL_ENABLED=0`

## Smoke Paths

### 1. Login And Home

- [ ] Open `/login`.
- [ ] Log in as an existing user.
- [ ] Confirm the app lands on `/home`.
- [ ] Confirm Home renders without error notifications.

### 2. Explore And Detail

- [ ] Open `/explore`.
- [ ] Confirm course, video, article, and path content can render when present.
- [ ] Open one course detail route.
- [ ] Open one article or video detail route.
- [ ] Open one path detail route.

### 3. Share Learning Item

- [ ] Open `/share/item?type=course`.
- [ ] Create a course with title, URL, and required metadata.
- [ ] Confirm publish redirects back to Explore.
- [ ] Confirm the new item appears in Explore.

### 4. Share Mixed Path

- [ ] Open `/share/path`.
- [ ] Create a path with at least two mixed learning items.
- [ ] Confirm publish redirects back to Explore paths.
- [ ] Open the path detail route and confirm items render in order.

### 5. Review And Tracking

- [ ] Add or update a review on a learning item.
- [ ] Add or update a review on a path.
- [ ] Track a course.
- [ ] Confirm tracked progress appears on Home.

### 6. Teams

- [ ] Open `/teams`.
- [ ] Confirm the inbox/team activity view renders.
- [ ] Create or select a team if test data allows.
- [ ] Confirm shared activity can be viewed without page errors.

### 7. Admin

- [ ] Log in as an admin.
- [ ] Open `/admin/users`.
- [ ] Confirm user list renders.
- [ ] Confirm disabled/reset controls are visible and guarded for admin use.

## Pass Criteria

- No unhandled UI errors.
- No backend 500s in logs.
- Canonical routes are used; no legacy `/courses`, `/paths`, `/articles`, `/activity`, or `/insights` route is required.
- Gated features stay hidden unless explicitly enabled.
