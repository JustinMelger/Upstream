# Learning Hub

A simple internal website where colleagues can browse a curated list of courses and jump to the provider.

## Functional requirements

### Core experience
- Browse a curated catalog of courses.
- Search and filter by provider, category, and level.
- Open a course link in one click.

### Course management
- Add new courses through an admin-friendly interface.
- Edit and remove existing courses.
- Store course data in a durable store (CSV initially, optionally SQLite later).

### Colleague tracking
- Each colleague can mark interest or completion per course.
- View progress per colleague.
- Aggregate insights (e.g., most popular courses, completion rates).

### Authentication
- Simple authentication required for access.
- Separate roles:
  - Admin/curator: manage courses and view aggregate stats.
  - Colleague: browse and track their own progress only.

### Learning paths
- Curate different learning paths (e.g., Onboarding, Data, Leadership).
- Each path groups courses in a recommended sequence.
- Colleagues can select a path and see their progress within it.

## Non-functional requirements (lightweight)
- Fast, simple UI for internal use.
- Easy to update without code changes.
- Works on modern browsers.

## Out of scope (for now)
- External SSO integrations.
- Complex permissions or team hierarchies.
- Paid course management or license tracking.

## Roadmap

### Phase 1 — MVP catalog
- Stable data model for courses (CSV-based).
- Search + filter UI.
- One-click course links.
- Basic “Add course” form for curators.

### Phase 2 — Management + paths
- Edit/delete courses.
- Learning paths with ordered sequences.
- Path overview page with progress per path.

### Phase 3 — Colleague tracking + auth
- Lightweight authentication (password or invite code).
- Colleague profiles with interest/completion tracking.
- Basic analytics (popular courses, completion rates).

### Phase 4 — Data durability + polish
- Migrate from CSV to SQLite.
- Import/export tools for course data.
- UI polish + accessibility improvements.
