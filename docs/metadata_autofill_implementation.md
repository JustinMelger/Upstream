> Implementation history, catalogued 2026-09-11. This records its delivery milestone; later refinements supersede earlier behavior and check counts. See [current guidance](README.md).

# V1 metadata autofill

New course, article, and video forms offer **Fetch details** beside the URL on desktop and below it on mobile. This explicit action fills untouched empty fields from page-authored metadata. Courses/videos receive title, description, and declared provider; articles receive title and description. Editing and paths retain manual entry.

## Form behavior

Existing input is preserved, including fields typed and then cleared while a request is pending. URL/type changes, navigation, publication attempts, and draft restore/discard invalidate pending responses. Successful suggestions update the live preview and existing version-one session draft. Users review and publish explicitly. The original resource URL is preserved across source redirects.

Fetching never fills recommendation notes, categories, tags, artwork, or content type. Success and empty-result feedback are announced politely. Failures stay local to the URL controls with retry and manual sharing available. Fetching does not disable the rest of the form.

## API and security

The existing authenticated `POST /url-preview/metadata` route is registered and covered by browser CSRF enforcement. Its existing wire structure is retained; image and classification fields remain empty. OpenAPI and TypeScript contracts are regenerated. No migration or content mutation contract changes are required.

Extraction prefers Open Graph titles, then Twitter titles, then HTML title. Descriptions prefer Open Graph, standard description, then Twitter. Provider comes only from declared `og:site_name`. Text is entity-decoded, stripped of markup, whitespace-normalized, and limited to 300 characters for title/provider and 2,000 for descriptions.

The dedicated metadata fetch path validates HTTP/HTTPS destinations with standard ports and no credentials. DNS answers must all be public. Connections use a validated numeric address, with the original Host header and TLS verification hostname retained. Each of at most three redirects is revalidated; redirect bodies are not consumed. No session credentials, cookies, environment proxies, or client-level URL logging are used.

A ten-second overall deadline includes DNS, queueing, redirects, and body reads; individual network operations have four-second timeouts. Responses are streamed with a one-megabyte body limit and accepted only as HTML/XHTML. The client requests identity encoding and rejects compressed responses rather than risking unbounded decompression; sites that ignore this request require manual entry. Concurrency is capped at four per API process, with at most 256 successful cached results for fifteen minutes. Failures expose generic errors without destination details.

The subsequent [v1 cleanup](v1_cleanup.md) removes the legacy external-image fetcher and `METADATA_AUTOFILL` setting. Explicit Fetch details remains available. Catalog/detail reads do not trigger metadata fetching. No generated summaries, scraping browser, runtime artwork fetching, or AI calls are introduced.

## Verification

- Full backend suite: 200 passing tests; three additional focused tests pass for overall DNS deadline, concurrency cap, and public IPv6 pinning. The focused metadata/security suite contains 34 passing tests.
- Frontend: 38 unit tests and 33 browser scenarios pass, including untouched-field preservation, stale responses, draft/preview recovery, new-only visibility, and publication after fetch failure.
- Visual coverage expands to 66 screen/state/viewport combinations, including metadata success/failure at 390px, 768px, and 1440px, plus existing Share and product regression coverage.
- Frontend lint, formatting, typing/build; backend Ruff, mypy, import boundaries; and OpenAPI contract verification pass.

Network safety and extraction tests use controlled fixtures, not public website availability. The v1 limitation is intentional: pages requiring JavaScript, authentication, or non-identity content encoding may need manual entry.

## Preview and rollback

Rebuild the existing frontend and backend Docker images together and refresh http://localhost:18080 without reseeding its database. Prior images are retained as `learning-react-ui:before-metadata-autofill` and `learning-react-api:before-metadata-autofill`. Rollback replaces images only. No production deployment or schema change is part of this implementation.
