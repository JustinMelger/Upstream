# Recommendation Persistence Cleanup

This note captures the remaining post-release cleanup related to the removed recommendation feature.

## Current State

- recommendation UI has been removed
- recommendation backend APIs/services have been removed
- recommendation activity/notification behavior has been removed
- recommendation ORM/data-model definitions still exist in the repo
- recommendation tables may still exist in existing databases

## Why This Was Not Part Of The V1 Cut

The v1 release decision was to remove recommendation behavior from the live product surface without bundling a schema-removal migration into the same stabilization window.

That keeps the release focused on:

- product-surface correctness
- auth/security fixes
- regression stability

## Post-Release Options

1. Leave the dormant tables in place temporarily if they are harmless operationally.
2. Remove the ORM/data-model definitions once the team is ready to retire the schema.
3. Add a migration that drops the recommendation tables after confirming no production dependency remains.

## Suggested Cleanup Order

1. Remove remaining architecture-doc references that describe recommendations as current behavior.
2. Add and apply schema migration to drop recommendation tables.
3. Remove any migration/test artifacts that only existed for recommendation persistence.
