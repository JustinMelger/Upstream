# V1 Release Notes

Learning Hub v1 ships a narrow, stable product:

- authenticated users can share courses, articles, videos, and mixed learning paths
- users can browse Explore, review learning items and paths, and track course/path progress
- Teams is a basic workspace for membership, inbox, and team activity
- admin users can manage user accounts

Not part of the v1 product:

- recommendation flows
- AI Curator as a core feature
- broader team collaboration features such as invitations, review requests, discussions, or audience-scoped sharing

Release-specific decisions:

- `FEATURE_AI_CURATOR` is off by default
- URL metadata/autofill remains enabled and has been hardened for v1
- `docs/v1/` is the release source of truth; `docs/roadmap.md` is post-v1 strategy
