# V1 Feature Matrix

This matrix maps the intended v1 feature set to the current implementation.

## Status Key

- `keep`: part of the supported v1 release
- `keep_with_fixes`: part of v1, but release blockers remain
- `defer`: present in code/docs, but not part of the supported v1 release
- `cleanup`: not a canonical shipped feature and should be removed or ignored

| Feature | Backend Contract | Frontend Contract | Data Model | Auth / Permissions | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Auth and sessions | `/auth/login`, `/auth/me`, `/auth/logout`, `/auth/role` | `/login`, guarded app routes | `users`, `sessions` | session token required after login | `keep_with_fixes` | username normalization bug must be fixed before release |
| Admin user management | `/auth/users`, `/auth/users/reset`, `/auth/users/disable`, `/auth/users/{username}` | `/admin/users` | `users` | admin only | `keep` | basic role model is stable enough for v1 |
| Courses | `/courses`, course reviews | `/share/item?type=course`, `/explore`, `/explore/courses/{id}` | `courses`, related review/tracking tables | authenticated create; owner/admin mutate | `keep` | this is one of the strongest parts of the current product |
| Articles | `/articles`, article reviews | `/share/item?type=article`, `/explore`, `/explore/articles/{id}` | `articles`, `article_reviews` | authenticated create; owner/admin mutate where supported | `keep` | keep expectations narrow: reviews only |
| Videos | `/videos`, video reviews | `/share/item?type=video`, `/explore`, `/explore/videos/{id}` | `videos`, `video_reviews` | authenticated create; owner/admin mutate where supported | `keep` | keep expectations narrow: reviews only |
| Learning paths | `/paths`, path reviews, path select/status endpoints | `/share/path`, `/explore/paths/{id}` | `paths`, `path_items`, `user_paths`, `path_reviews` | authenticated create; owner/admin mutate | `keep` | mixed-item paths are part of the v1 contract |
| Tracking | `/tracking`, `/tracking/stats`, `/tracking/stats/users` | learning/home/profile surfaces | `tracking`, `user_paths` | self-service for own tracking, authenticated users can view aggregate team totals | `keep` | v1 scope is courses plus selected path progress only |
| Teams | `/teams`, `/teams/mine`, `/teams/{id}`, member endpoints, `/teams/{id}/activity` | `/teams` | `teams`, `team_members` | member-only team workspace visibility; owner/admin member management | `keep` | treat as basic workspace and activity lens, not full collaboration or private catalog |
| Notifications/activity | `/notifications`, team activity composition | `/teams`, home/learning activity panels | derived event data | authenticated | `keep` | keep mailbox/activity usage simple for v1 |
| Course/path recommendations | no live v1 API surface | removed from the released frontend | `course_recommendations`, `path_recommendations` tables still exist | n/a | `defer` | cut from v1 because it overlaps confusingly with reviews; remaining table cleanup is post-release persistence work |
| URL metadata/preview | `/url-preview/metadata` | share form autofill | no durable canonical table yet | authenticated | `keep_with_fixes` | SSRF hardening required, or disable for v1 |
| AI Curator | `/ai/plan` | `/ai` when feature-flagged | none; draft only | authenticated | `defer` | deterministic placeholder, not a stable v1 capability |
| Team audience/scoped sharing | partial roadmap only | not canonical | not fully present | n/a | `defer` | do not describe as a v1 feature; Explore remains globally visible in v1 |
| Review requests/discussions | roadmap only | not canonical | not fully present | n/a | `defer` | not ready for v1 |
| Old activity page implementation | duplicate `/teams` route implementation in `pages/activity` | not registered in app | none | n/a | `cleanup` | dead/stale implementation should not be treated as shipped |

## Release Interpretation

The v1 release should be based on the rows marked `keep` and `keep_with_fixes`.

Rows marked `defer` should remain out of the release narrative even if code exists.

Rows marked `cleanup` should be removed or ignored so the shipped product has one canonical implementation path per feature.
