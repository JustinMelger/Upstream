"""Bounded SQL projections for discovery, personal learning, and shared activity."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, case, cast, Float, func, literal, or_, select, String, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.orm_models import (
    Article,
    ArticleReview,
    Course,
    CourseReview,
    Path,
    PathItem,
    PathReview,
    Tracking,
    UserPath,
    Video,
    VideoReview,
)


CONTENT: dict[str, Any] = {"course": Course, "article": Article, "video": Video, "path": Path}
REVIEWS: dict[str, Any] = {"course": CourseReview, "article": ArticleReview, "video": VideoReview, "path": PathReview}


def catalog_source() -> Any:
    """Build a uniform projection without materializing entire catalogs in Python."""
    statements = []
    for kind, model in CONTENT.items():
        review = REVIEWS[kind]
        foreign_key = getattr(review, f"{kind}_id")
        ratings = (
            select(
                foreign_key.label("content_id"),
                func.avg(review.rating).label("rating"),
                func.count(review.id).label("review_count"),
            )
            .group_by(foreign_key)
            .subquery()
        )
        statements.append(
            select(
                literal(kind).label("type"),
                model.id,
                (model.name if kind == "path" else model.title).label("title"),
                getattr(model, "description", literal("")).label("description"),
                func.coalesce(getattr(model, "provider", literal("")), "").label("provider"),
                func.coalesce(getattr(model, "category", literal("")), "").label("category"),
                func.coalesce(getattr(model, "level", literal("")), "").label("level"),
                cast(getattr(model, "duration_hours", literal(None)), Float).label("duration_hours"),
                getattr(model, "url", literal("")).label("url"),
                model.created_by,
                model.created_at,
                model.recommendation_note,
                func.coalesce(ratings.c.rating, 0.0).label("rating"),
                func.coalesce(ratings.c.review_count, 0).label("review_count"),
            ).outerjoin(ratings, ratings.c.content_id == model.id)
        )
    return union_all(*statements).subquery("catalog")


def filter_catalog(statement: Any, columns: Any, filters: dict[str, Any]) -> Any:
    """Apply the same content filters to results and facet options."""
    if filters.get("q"):
        needle = str(filters["q"]).strip()
        statement = statement.where(
            or_(
                columns.title.icontains(needle, autoescape=True),
                columns.description.icontains(needle, autoescape=True),
                columns.recommendation_note.icontains(needle, autoescape=True),
            )
        )
    for field in ("type", "provider", "category", "created_by"):
        value = filters.get("author" if field == "created_by" else field)
        if value:
            statement = statement.where(columns[field] == value)
    return statement


class WorkspaceRepository:
    """Read models with server-side filters, ordering, totals, and pagination."""

    def __init__(self, session: AsyncSession):
        """Bind projections to the request transaction."""
        self.session = session

    async def _page(self, statement: Any, page: int, page_size: int) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
        result = await self.session.execute(statement.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": [dict(row) for row in result.mappings()],
            "total": int(total or 0),
            "page": page,
            "page_size": page_size,
        }

    async def catalog(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Filter all subtypes before globally sorting and paginating."""
        c = catalog_source().c
        statement = filter_catalog(select(c), c, filters)
        sort = filters.get("sort", "newest")
        order = {
            "title": [func.lower(c.title).asc()],
            "rating": [c.rating.desc(), c.review_count.desc()],
            "newest": [c.created_at.desc().nulls_last()],
        }
        return await self._page(statement.order_by(*order[sort], c.type, c.id.desc()), filters["page"], filters["page_size"])

    async def facets(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Exclude a facet's own value so it remains possible to change the selection."""
        c = catalog_source().c
        field = filters["field"]
        value = c[field]
        statement = filter_catalog(select(value.label("value")).distinct(), c, filters | {field: ""})
        statement = statement.where(func.trim(value) != "")
        if filters.get("option_q"):
            statement = statement.where(value.icontains(filters["option_q"].strip(), autoescape=True))
        page = await self._page(statement.order_by(value), filters["page"], filters["page_size"])
        page["items"] = [row["value"] for row in page["items"]]
        return page

    async def learning_items(self, username: str, filters: dict[str, Any]) -> dict[str, Any]:
        """Read one personal collection using a fixed number of SQL statements."""
        c = catalog_source().c
        view = filters["view"]
        statement = select(c, literal(None, String).label("status"))
        if view == "contributions":
            statement = statement.where(c.created_by == username).order_by(c.created_at.desc().nulls_last())
        elif view == "paths":
            statement = (
                select(c, UserPath.status)
                .join(UserPath, and_(c.type == "path", UserPath.path_id == c.id))
                .where(UserPath.colleague_id == username)
                .order_by(UserPath.created_at.desc())
            )
        else:
            statement = (
                select(c, Tracking.status)
                .join(Tracking, and_(c.type == "course", Tracking.course_id == c.id))
                .where(Tracking.colleague_id == username)
                .order_by(Tracking.updated_at.desc())
            )
            if filters.get("status"):
                statement = statement.where(Tracking.status == filters["status"])
        if filters.get("content_id"):
            statement = statement.where(c.id == filters["content_id"])
        page = await self._page(statement.order_by(c.type, c.id), filters["page"], filters["page_size"])
        if view == "paths" and page["items"]:
            ids = [row["id"] for row in page["items"]]
            totals = (
                (
                    await self.session.execute(
                        select(
                            PathItem.path_id,
                            func.count().label("total"),
                            func.sum(case((Tracking.status == "completed", 1), else_=0)).label("completed"),
                        )
                        .join(Course, Course.id == PathItem.item_id)
                        .outerjoin(Tracking, and_(Tracking.course_id == PathItem.item_id, Tracking.colleague_id == username))
                        .where(PathItem.path_id.in_(ids), PathItem.item_type == "course")
                        .group_by(PathItem.path_id)
                    )
                )
                .mappings()
                .all()
            )
            by_path = {row["path_id"]: {"completed": row["completed"], "total": row["total"]} for row in totals}
            for item in page["items"]:
                item["course_progress"] = by_path.get(item["id"], {"completed": 0, "total": 0})
        return page

    async def summary(self, username: str) -> dict[str, Any]:
        """Return personal totals and one deterministic next action."""
        counts: dict[str, int] = dict(
            (
                await self.session.execute(
                    select(Tracking.status, func.count()).where(Tracking.colleague_id == username).group_by(Tracking.status)
                )
            )
            .tuples()
            .all()
        )
        selected = await self.session.scalar(
            select(func.count()).select_from(UserPath).where(UserPath.colleague_id == username)
        )
        c = catalog_source().c
        contributions = await self.session.scalar(select(func.count()).select_from(c.id.table).where(c.created_by == username))
        next_row = (
            (
                await self.session.execute(
                    select(Course.id, Course.title, Course.url, Course.provider, Course.duration_hours, Tracking.status)
                    .join(Tracking, Tracking.course_id == Course.id)
                    .where(Tracking.colleague_id == username, Tracking.status == "in_progress")
                    .order_by(Tracking.updated_at.desc(), Course.id)
                    .limit(1)
                )
            )
            .mappings()
            .first()
        )
        if not next_row:
            latest_path = (
                select(UserPath.path_id)
                .where(UserPath.colleague_id == username)
                .order_by(UserPath.created_at.desc(), UserPath.path_id.desc())
                .limit(1)
                .scalar_subquery()
            )
            next_row = (
                (
                    await self.session.execute(
                        select(Course.id, Course.title, Course.url, Course.provider, Course.duration_hours, Tracking.status)
                        .join(PathItem, and_(PathItem.item_type == "course", PathItem.item_id == Course.id))
                        .outerjoin(Tracking, and_(Tracking.course_id == Course.id, Tracking.colleague_id == username))
                        .where(PathItem.path_id == latest_path, or_(Tracking.status.is_(None), Tracking.status != "completed"))
                        .order_by(PathItem.position.asc().nulls_last(), PathItem.id)
                        .limit(1)
                    )
                )
                .mappings()
                .first()
            )
        return {
            "interested": counts.get("interested", 0),
            "in_progress": counts.get("in_progress", 0),
            "completed": counts.get("completed", 0),
            "selected_paths": int(selected or 0),
            "contributions": int(contributions or 0),
            "next_course": dict(next_row) if next_row else None,
        }

    async def path_progress(self, username: str, path_id: int) -> dict[str, Any]:
        """Return course-only progress and independent selection state for a path."""
        selected = (
            await self.session.execute(select(UserPath).where(UserPath.path_id == path_id, UserPath.colleague_id == username))
        ).scalar_one_or_none()
        rows = (
            (
                await self.session.execute(
                    select(PathItem.item_id.label("id"), Tracking.status)
                    .outerjoin(Tracking, and_(Tracking.course_id == PathItem.item_id, Tracking.colleague_id == username))
                    .where(PathItem.path_id == path_id, PathItem.item_type == "course")
                    .order_by(PathItem.position, PathItem.id)
                )
            )
            .mappings()
            .all()
        )
        return {
            "selected": selected is not None,
            "status": selected.status if selected else None,
            "courses": [dict(row) for row in rows],
            "completed": sum(row["status"] == "completed" for row in rows),
            "total": len(rows),
        }

    async def activity(self, username: str, filters: dict[str, Any]) -> dict[str, Any]:
        """Page globally merged share/review events with explicit visibility."""
        statements = []
        for kind, model in CONTENT.items():
            title = model.name if kind == "path" else model.title
            note = func.nullif(func.regexp_replace(model.recommendation_note, r"^\s+|\s+$", "", "g"), "")
            description = func.nullif(func.regexp_replace(model.description, r"^\s+|\s+$", "", "g"), "")
            if filters["scope"] == "shared":
                statements.append(
                    select(
                        (literal(f"share:{kind}:") + cast(model.id, String)).label("event_id"),
                        literal("share").label("event_type"),
                        literal(kind).label("type"),
                        model.id.label("content_id"),
                        title.label("title"),
                        model.created_by.label("actor"),
                        model.created_at.label("happened_at"),
                        literal(None, Float).label("rating"),
                        func.coalesce(note, description).label("excerpt"),
                        case((note.is_not(None), "recommendation"), (description.is_not(None), "description")).label(
                            "excerpt_kind"
                        ),
                    ).where(model.created_at.is_not(None), model.created_by.is_not(None))
                )
            review = REVIEWS[kind]
            statement = select(
                (literal(f"review:{kind}:") + cast(review.id, String)).label("event_id"),
                literal("review").label("event_type"),
                literal(kind).label("type"),
                model.id.label("content_id"),
                title.label("title"),
                review.created_by.label("actor"),
                review.created_at.label("happened_at"),
                cast(review.rating, Float).label("rating"),
                func.nullif(func.regexp_replace(review.text, r"^\s+|\s+$", "", "g"), "").label("excerpt"),
                literal("review").label("excerpt_kind"),
            ).join(model, getattr(review, f"{kind}_id") == model.id)
            if filters["scope"] == "personal":
                statement = statement.where(model.created_by == username, review.created_by != username)
            statements.append(statement)
        events = union_all(*statements).subquery("events")
        return await self._page(
            select(events).order_by(events.c.happened_at.desc(), events.c.event_id), filters["page"], filters["page_size"]
        )
