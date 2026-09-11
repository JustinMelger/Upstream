# V1 cleanup implementation record

Completed 2026-09-11. This is a behavior-preserving cleanup of the React pilot, following the metadata and forty-cover artwork releases. Current contributor instructions start at the [documentation index](README.md).

## Scope and working-tree protection

The initial inventory contained 463 status entries, including uncommitted redesign work and previously removed NiceGUI files. Those existing changes were retained. No Git reset, untracked-file purge, broad refactor, release-version change, migration edit, or production deployment was performed.

Cleanup-specific code changes are confined to the metadata/content services and their dependency wiring, the obsolete setting, focused service tests, four unused imports, Python dependency declarations/lockfile, and project description. Documentation, ignore rules, CI, and task-runner changes are listed below. Existing frontend implementation, artwork, generated API contracts, and reviewed visual baselines remain unchanged.

## Removed and retained code

- Removed YouTube/Vimeo thumbnail resolution, Open Graph image fetching, image URL validation/resolution helpers, image cache/lock, and inferred provider/type/category/tag helpers.
- Removed preview-service injection and image-resolution fan-out from course, article, and video reads, plus the obsolete `metadata_autofill` setting. Removed five dedicated image-resolver tests and replaced content image-resolution tests with three no-outbound-HTTP read checks.
- Preserved explicit authenticated Fetch details, its hardened fetcher, bounded metadata cache/concurrency, extraction precedence, and request/response contracts. Preview-image and inferred classification fields keep their existing empty defaults wherever exposed.
- Removed unused direct pandas, requests, and Python Playwright requirements. The lock update removed eight packages without upgrading retained packages. `requests` remains transitively required by retained telemetry/audit tooling; Node Playwright remains the browser/visual test runner. Pillow remains for artwork tooling. Release versions are unchanged.
- Removed unused imports in the workspace repository and two test modules. Larger module restructuring remains deferred.

## Documentation and tooling

README now provides concise setup and development instructions. [Operations](operations.md) consolidates contracts, checks, and rollback. [The documentation index](README.md) distinguishes current guidance, implementation history, and approved design/artwork references.

Superseded NiceGUI/Teams/pre-React specifications moved into [the archive](archive/README.md); former high-level entries forward there. Historical content and useful evidence remain available. Implementation records are explicitly historical; current architecture describes active Fetch details and forty local covers. A pre-existing link to an absent OIDC proposal is now labeled as an unavailable historical reference.

CI now checks frontend formatting. Task-runner and shell quality gates include formatting and use consistent lint/audit scope. Ignore rules cover caches, reports, build output, and local secrets without deleting untracked work. Artwork, generation records, mockups, migrations, lockfiles, contracts, and baselines were retained.

## Verification

| Check | Result |
| --- | --- |
| Backend regression suite | 196 passed |
| Focused final content/metadata checks | 44 passed after final simplification/import cleanup |
| Ruff lint and formatting | Passed |
| mypy | Passed, 78 source files |
| Import boundaries | Both contracts passed |
| Python and npm dependency audits | No known vulnerabilities reported |
| Frontend formatting, lint, types, build | Passed |
| Frontend unit tests | 39 passed |
| Browser workflows | 33 passed |
| Pinned visual comparisons | 66 passed; no baseline updates |
| OpenAPI and generated TypeScript | No drift; generated types byte-identical |
| Repository Markdown file links | Checked after archive relocation |
| Active setup/operations/architecture instructions | No machine-specific temporary paths or retired commands |
| Fresh Docker installation | Separate `learning-v1-cleanup-smoke` project, new volume, database port 55433 and UI port 18081; migrations through `20260909_0019`, login, sharing, Interested → In progress → Completed, catalog/detail reads, retired-route error, and logout passed |
| Populated migration verifier | Separate empty migration-test database; all original records across 14 legacy tables preserved |
| Local preview | Rebuilt and verified at `http://localhost:18080`; existing database reused, no reseeding |

The first fresh-install smoke harness incorrectly expected a course API image field that the unchanged schema does not expose; the assertion was corrected to check the existing detail contract. Subsequent duplicate attempts confirmed existing duplicate protection before the final complete smoke pass. These were harness corrections, not product changes.

The disposable installation project and its test volume were removed after verification; the retained preview project was not part of that teardown.

## Compatibility and rollback

Header authentication and retained team tables remain available during the rollback window. Historical migrations are unchanged. The removed external-image fetcher is not needed for rollback using previous images.

Previous preview images are retained as `learning-react-api:before-v1-cleanup` and `learning-react-ui:before-v1-cleanup`. The current images were rebuilt and the existing preview project refreshed without replacing its database volume. Standard Docker installation remains on port 8080; port 18080 is the separate developer preview.

## Deferred work

Large service/page decompositions, future image uploads, broader metadata suggestions, telemetry changes, team-table removal, and authentication compatibility retirement require separate decisions after the pilot. No new product behavior or production release was included.
