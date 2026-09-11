"""Read-only orchestration for the learning workspace."""

from backend.database.async_repositories.workspace import WorkspaceRepository
from backend.database.tx import session_scope


class WorkspaceService:
    """Keep transaction ownership out of transport handlers."""

    def __init__(self, repo: WorkspaceRepository):
        """Bind a request-scoped repository."""
        self.repo = repo

    async def catalog(self, filters: dict) -> dict:
        """Read one filtered catalog page."""
        async with session_scope(self.repo.session):
            return await self.repo.catalog(filters)

    async def learning_items(self, username: str, filters: dict) -> dict:
        """Read a collection restricted to the authenticated user."""
        async with session_scope(self.repo.session):
            return await self.repo.learning_items(username, filters)

    async def facets(self, filters: dict) -> dict:
        """Read bounded discovery options."""
        async with session_scope(self.repo.session):
            return await self.repo.facets(filters)

    async def summary(self, username: str) -> dict:
        """Read personal totals and a next course."""
        async with session_scope(self.repo.session):
            return await self.repo.summary(username)

    async def path_progress(self, username: str, path_id: int) -> dict:
        """Read a user's progress within a mixed path."""
        async with session_scope(self.repo.session):
            return await self.repo.path_progress(username, path_id)

    async def activity(self, username: str, filters: dict) -> dict:
        """Read only events allowed by the requested visibility scope."""
        async with session_scope(self.repo.session):
            page = await self.repo.activity(username, filters)
            for event in page["items"]:
                excerpt = (event.get("excerpt") or "").strip()
                event["excerpt"] = excerpt[:279].rstrip() + "…" if len(excerpt) > 280 else excerpt or None
                if not excerpt:
                    event["excerpt_kind"] = None
            return page
