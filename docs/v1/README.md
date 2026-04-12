# V1 Product Spec

This folder defines the release scope for the first stable version of Learning Hub.

The goal is to describe the product that will be supported in production, not every feature that exists in the repository.

## V1 Principles

- Keep the release centered on basic learning workflows.
- Ship only features with a clear user outcome, stable route/API contract, and test coverage.
- Treat unfinished, placeholder, or high-risk features as deferred even if code exists.
- Prefer explicit exclusions over ambiguous “maybe in v1” scope.

## V1 Feature Set

- [Auth And Users](./auth_and_users.md)
- [Learning Items](./learning_items.md)
- [Paths](./paths.md)
- [Reviews](./reviews.md)
- [Tracking](./tracking.md)
- [Teams](./teams.md)

## Deferred Or Experimental

- [Deferred Features](./deferred_features.md)

## Release Planning Aids

- [Feature Matrix](./feature_matrix.md)
- [Release Gaps](./release_gaps.md)
- [Release Checklist](./release_checklist.md)
- [Dead Code And Hidden Features](./dead_code_and_hidden_features.md)

## Focused Technical Notes

- [Technical Design: Auth And Sessions](./technical_auth.md)
- [Technical Design: Learning Items](./technical_learning_items.md)
- [Technical Design: Teams And Activity](./technical_teams.md)

## Release Definition

Learning Hub v1 is a learning-sharing platform where authenticated users can:

- log in and manage sessions
- share courses, articles, and videos
- browse shared learning items
- build mixed learning paths
- review learning items and paths
- track course progress and path progress
- use basic teams for membership and team activity
- administer users as an admin

## Exit Criteria

V1 is ready only when:

- the features above have aligned UI, API, and docs behavior
- release-blocking auth and security defects are fixed
- deferred features are not presented as core product capabilities
- the README and roadmap describe the same shipped scope
