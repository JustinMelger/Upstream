# Upstream product guide

Upstream is a shared learning library for courses, articles, videos and ordered paths. Accounts are managed by administrators. Content is shared across the application; personal learning state belongs to each account.

## Explore

Search the full library and filter by content type, provider, category or author. Sort by newest, title or rating. Provider and category selectors search available options. Mobile advanced filters apply when you select Apply; cancelling leaves existing filters intact.

Explore fetches 24 resources per page, with Previous/Next controls and a total count. A result set of 100 courses spans five pages: 24 on each of the first four and four on the last. Search and filters apply before server-side pagination, and the page and filters are recorded in the URL.

The unfiltered first page, sorted newest first, promotes one of those resources into a spotlight. That resource is counted once and is excluded from the grid. Later pages, searches and filters use the regular grid.

## My learning and paths

Add courses to My learning, continue them, and set Interested, In progress or Completed. Starting a course can save In progress and open its external resource; completion is explicit. Reopening a completed course does not reset progress. Successful completion offers an Undo action for the current session. Failed changes retain the previous saved status and allow retry.

Paths contain an ordered mix of courses, articles and videos. Select a path and set its manual status independently. The completion count includes courses only; articles and videos do not support completion tracking. A path with no courses has no course-completion percentage. Collections are paginated, and counts link to filtered views.

## Activity and profile

For you shows other people's reviews on content you shared. Shared activity shows content shares and reviews across the library. Both feeds use 24 events per page, with Previous/Next controls. Events are projections of current content and reviews, not an immutable historical log.

My stats shows current personal totals rather than a paginated feed. Profile shows account information, linked personal totals and the three latest contributions. Shared Activity does not expose other users' course tracking or personal path progress.

## Sharing and reviews

Share courses, articles and videos by URL, or assemble a path from existing resources. Forms support descriptions, an optional plain-text recommendation note and a live preview. Sharing a course is independent of adding it to personal learning. Content owners and administrators can edit or delete resources. Removing a referenced resource removes its path references without deleting the path.

New course, article and video forms offer optional Fetch details from page-authored metadata. Suggestions fill only untouched empty fields; manual entry and publication remain available after a fetch failure. Editing and path creation use manual entry. Artwork is assigned automatically from the bundled library.

Share/edit forms save drafts in the current browser session and offer Restore or Discard when reopened. Drafts do not synchronize across devices. Publication, discard, logout and account changes clear the relevant drafts; session expiry preserves drafts for the same account after sign-in. Storage failures leave the form usable.

Resources support ratings and written reviews. Review removal is restricted to the review author or an administrator. Content, reviews and recommendation attribution are shared; account sessions and draft storage are not public.

## Administration and access

Administrators create accounts, search users, reset passwords, enable or disable accounts, and delete accounts according to server policy. Self-disable and self-delete are unavailable. Password reset and account disable revoke affected sessions. Members cannot access administrative account or aggregate/user-statistics endpoints.

See [operations](operations.md) for authentication, API contracts and deployment, and [artwork guidance](artwork/README.md) for how covers are assigned.
