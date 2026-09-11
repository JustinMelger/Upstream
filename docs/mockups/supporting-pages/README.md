# Supporting-page visual proposals

Five desktop/mobile design boards extending the implemented Explore design. Generated with the built-in image generation tool using `frontend/react/tests/visual/baselines/explore-1440.png` as the visual reference. These are proposed compositions, not implemented screens or verified responsive screenshots. Names, content, ratings, dates, and counts are illustrative.

The approved direction is now implemented; see the [implementation and verification record](../../supporting_pages_implementation.md). The images remain concept references. Actual reviewed browser baselines are in `frontend/react/tests/visual/baselines/`.

## Selected boards

- [Resource details](resource-details-v2.png): a compact introduction, immediate learning actions, an attributed recommendation, and readable reviews. Mobile uses a thumbnail so actions appear early. Apply the same introduction to articles/videos with their respective accents and no tracking controls.
- [Path details](path-details-v2.png): lavender artwork, independent manual status, course-only progress, and an ordered mixed-resource collection.
- [Activity](activity.png): artwork-supported share/review rows with explicit authors, dates, and ratings. The selected view is Shared activity; For you reuses the feed with its existing private filtering, while My stats retains current personal totals.
- [Profile](profile.png): personal identity, compact linked learning totals, and a contribution library.
- [Admin](admin.png): a clear account list with contextual actions and a focused account-creation form. Mobile uses stacked account rows.

Exact initial prompts are in the matching `*.prompt.txt` files. The two detail boards have additional `*-v2.prompt.txt` editing prompts; their original boards remain for provenance. All image outputs are saved in this directory. No runtime application files were changed.

## Implementation review notes

- Preserve actual server permissions. Resource edit/delete actions appear only for authorized owners/admins; the selected resource mockup shows a reader view. Review forms, deep links, confirmations, empty/error states and keyboard behavior still need their existing implementation.
- The Admin illustration has inherited the AL account initials and Explore highlight from the reference. The implemented Admin screen must use the authenticated administrator identity, avoid highlighting Explore, and retain protections against self-disable/delete. Search and Manage are proposed UI organization over existing account operations, not new permissions.
- Sample authors differ between boards; do not import these mock values. Keep deterministic artwork and real author/rating/count data across actual pages.
- Activity illustrates four rows from a larger collection. Its sample pagination label is illustrative; calculate page counts from the real page size and total, hiding pagination on a single page. Use tighter thumbnails if production feed density needs it.
- The mobile path illustration uses compact status icons. Implementation must expose accessible status names and preferably visible text rather than relying on icon/color recognition.
- Profile totals remain self-only. Contributions reuse bounded collection reads; no public profile, followers, avatar upload, biography, or historical analytics is implied.
- The boards are scaled design references, not pixel measurements or accessibility evidence. Verify real 390px/768px/1440px layouts, minimum touch sizes, contrast, focus, long content, and missing artwork during implementation.
