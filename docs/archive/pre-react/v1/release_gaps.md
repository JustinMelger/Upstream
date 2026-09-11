# V1 Release Gaps

This file lists the most important gaps between the intended v1 product and the current implementation.

## Release Blockers

| Area | Current Gap | Risk | Decision Needed |
| --- | --- | --- | --- |
| Auth | username normalization is inconsistent across login, lookup, and session creation | users can fail login unexpectedly and auth behavior leaks implementation details | fix before release |
| URL metadata | metadata fetch flow is exposed to authenticated users without sufficient SSRF hardening | security issue in a non-core support feature | harden or disable before release |
| Product scope | docs, roadmap, and code contain more capability than the stable product should promise | feature creep continues and v1 remains ambiguous | freeze v1 scope in docs and release notes |

## Important Non-Blockers

| Area | Current Gap | Risk | Decision Needed |
| --- | --- | --- | --- |
| Teams | basic team workspace is present, but broader collaboration ideas are mixed into roadmap/docs | users may assume richer team features exist | describe teams narrowly in v1 |
| Learning item capability model | subtype behavior is asymmetric (`course` vs `article` vs `video`) | UI/docs can overpromise feature symmetry | keep the asymmetric model explicit |
| Recommendations | recommendation flows overlap conceptually with ratings/reviews and are not clearly surfaced as a distinct benefit | users may not understand why both exist | defer from v1 and keep reviews only |
| AI Curator | feature exists behind a flag, but behavior is placeholder/draft quality | users may treat it as a real planning engine | defer from v1 or label experimental |
| Metadata/autofill UX | share flows benefit from it, but core workflows should still work without it | support tooling becomes mistaken for required product behavior | treat as optional support behavior |

## Cleanup Gaps

| Area | Current Gap | Risk | Decision Needed |
| --- | --- | --- | --- |
| Frontend routes | duplicate `/teams` route implementation exists in old `activity` page code | confusion about canonical UI path | remove or archive non-canonical implementation |
| Docs | roadmap contains future-state items near the current v1 snapshot | release scope remains muddy | keep roadmap, but make `docs/v1/` the release source of truth |
| Feature flags | some flagged features are easy to expose accidentally | unstable features leak into release | define default release flags explicitly |

## Release Decision Rule

For each open gap, choose one of:

- `fix now`
- `disable for v1`
- `defer from v1 narrative`
- `cleanup after release`

Anything without a decision should be treated as not ready for v1.
