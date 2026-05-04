from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import TeamMemberRecord, TeamRecord
from backend.database.orm_models import (
    Article as ArticleModel,
    ArticleReview as ArticleReviewModel,
    Course as CourseModel,
    CourseReview as CourseReviewModel,
    PathReview as PathReviewModel,
    Team as TeamModel,
    TeamMember as TeamMemberModel,
    Video as VideoModel,
    VideoReview as VideoReviewModel,
)


class TeamsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of team persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with request-scoped session."""
        self.session = session

    async def create_team(
        self,
        *,
        name: str,
        description: str | None,
        owner_user_id: str,
        created_at: str | datetime,
        updated_at: str | datetime,
    ) -> int:
        """Create a team row and return its id."""
        team = TeamModel(
            name=name,
            description=description,
            owner_user_id=owner_user_id,
            created_at=self._as_datetime(created_at),
            updated_at=self._as_datetime(updated_at),
        )
        self.session.add(team)
        await self.session.flush()
        return int(team.id)

    async def get_team_by_id(self, *, team_id: int) -> TeamRecord | None:
        """Fetch one team by id."""
        result = await self.session.execute(select(TeamModel).where(TeamModel.id == int(team_id)).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return TeamRecord(
            id=int(row.id),
            name=str(row.name or ""),
            description=str(row.description) if row.description is not None else None,
            owner_user_id=str(row.owner_user_id or ""),
            created_at=self._as_iso_or_empty(row.created_at),
            updated_at=self._as_iso_or_empty(row.updated_at),
        )

    async def list_teams_for_user(self, *, user_id: str) -> list[TeamRecord]:
        """List teams where user is a member."""
        result = await self.session.execute(
            select(TeamModel)
            .join(TeamMemberModel, TeamMemberModel.team_id == TeamModel.id)
            .where(func.lower(TeamMemberModel.user_id) == func.lower(str(user_id)))
            .order_by(func.lower(TeamModel.name).asc(), TeamModel.id.asc())
        )
        rows = result.scalars().all()
        return [
            TeamRecord(
                id=int(row.id),
                name=str(row.name or ""),
                description=str(row.description) if row.description is not None else None,
                owner_user_id=str(row.owner_user_id or ""),
                created_at=self._as_iso_or_empty(row.created_at),
                updated_at=self._as_iso_or_empty(row.updated_at),
            )
            for row in rows
        ]

    async def create_member(
        self,
        *,
        team_id: int,
        user_id: str,
        role: str,
        created_at: str | datetime,
        updated_at: str | datetime,
    ) -> None:
        """Create team member row."""
        self.session.add(
            TeamMemberModel(
                team_id=int(team_id),
                user_id=str(user_id),
                role=str(role),
                created_at=self._as_datetime(created_at),
                updated_at=self._as_datetime(updated_at),
            )
        )

    async def get_member(self, *, team_id: int, user_id: str) -> TeamMemberRecord | None:
        """Fetch a specific team membership row."""
        result = await self.session.execute(
            select(TeamMemberModel)
            .where(TeamMemberModel.team_id == int(team_id))
            .where(func.lower(TeamMemberModel.user_id) == func.lower(str(user_id)))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return TeamMemberRecord(
            team_id=int(row.team_id),
            user_id=str(row.user_id or ""),
            role=str(row.role or "member"),
            created_at=self._as_iso_or_empty(row.created_at),
            updated_at=self._as_iso_or_empty(row.updated_at),
        )

    async def list_members(self, *, team_id: int) -> list[TeamMemberRecord]:
        """List members for a team."""
        result = await self.session.execute(
            select(TeamMemberModel)
            .where(TeamMemberModel.team_id == int(team_id))
            .order_by(
                TeamMemberModel.role.asc(),
                func.lower(TeamMemberModel.user_id).asc(),
            )
        )
        rows = result.scalars().all()
        return [
            TeamMemberRecord(
                team_id=int(row.team_id),
                user_id=str(row.user_id or ""),
                role=str(row.role or "member"),
                created_at=self._as_iso_or_empty(row.created_at),
                updated_at=self._as_iso_or_empty(row.updated_at),
            )
            for row in rows
        ]

    async def delete_member(self, *, team_id: int, user_id: str) -> int:
        """Remove one team member."""
        result = await self.session.execute(
            delete(TeamMemberModel)
            .where(TeamMemberModel.team_id == int(team_id))
            .where(func.lower(TeamMemberModel.user_id) == func.lower(str(user_id)))
        )
        return self._rowcount(result)

    async def update_member_role(self, *, team_id: int, user_id: str, role: str, updated_at: str | datetime) -> int:
        """Update role for an existing team member."""
        result = await self.session.execute(
            update(TeamMemberModel)
            .where(TeamMemberModel.team_id == int(team_id))
            .where(func.lower(TeamMemberModel.user_id) == func.lower(str(user_id)))
            .values(role=str(role), updated_at=self._as_datetime(updated_at))
        )
        return self._rowcount(result)

    async def count_members(self, *, team_id: int) -> int:
        """Count members in a team."""
        result = await self.session.execute(
            select(func.count(TeamMemberModel.id)).where(TeamMemberModel.team_id == int(team_id))
        )
        return int(result.scalar_one() or 0)

    async def list_team_activity_rows(self, *, team_id: int, limit: int) -> list[dict]:
        """Return recent team-scoped social activity events."""
        members_select = select(TeamMemberModel.user_id).where(TeamMemberModel.team_id == int(team_id))

        course_share_rows = await self.session.execute(
            select(
                CourseModel.id.label("event_id"),
                CourseModel.created_by.label("actor"),
                CourseModel.created_at.label("created_at"),
                CourseModel.id.label("target_id"),
                CourseModel.title.label("target_label"),
                literal("course").label("target_type"),
                literal("course_shared").label("event_type"),
            )
            .where(CourseModel.created_by.in_(members_select))
            .where(CourseModel.created_at.is_not(None))
            .order_by(CourseModel.created_at.desc(), CourseModel.id.desc())
            .limit(int(limit))
        )

        article_share_rows = await self.session.execute(
            select(
                ArticleModel.id.label("event_id"),
                ArticleModel.created_by.label("actor"),
                ArticleModel.created_at.label("created_at"),
                ArticleModel.id.label("target_id"),
                ArticleModel.title.label("target_label"),
                literal("article").label("target_type"),
                literal("article_shared").label("event_type"),
            )
            .where(ArticleModel.created_by.in_(members_select))
            .where(ArticleModel.created_at.is_not(None))
            .order_by(ArticleModel.created_at.desc(), ArticleModel.id.desc())
            .limit(int(limit))
        )

        video_share_rows = await self.session.execute(
            select(
                VideoModel.id.label("event_id"),
                VideoModel.created_by.label("actor"),
                VideoModel.created_at.label("created_at"),
                VideoModel.id.label("target_id"),
                VideoModel.title.label("target_label"),
                literal("video").label("target_type"),
                literal("video_shared").label("event_type"),
            )
            .where(VideoModel.created_by.in_(members_select))
            .where(VideoModel.created_at.is_not(None))
            .order_by(VideoModel.created_at.desc(), VideoModel.id.desc())
            .limit(int(limit))
        )

        course_review_rows = await self.session.execute(
            select(
                CourseReviewModel.id.label("event_id"),
                CourseReviewModel.created_by.label("actor"),
                CourseReviewModel.created_at.label("created_at"),
                CourseReviewModel.course_id.label("target_id"),
                literal("course").label("target_type"),
                literal("course_review").label("event_type"),
            )
            .where(CourseReviewModel.created_by.in_(members_select))
            .where(CourseReviewModel.created_at.is_not(None))
            .order_by(CourseReviewModel.created_at.desc(), CourseReviewModel.id.desc())
            .limit(int(limit))
        )

        path_review_rows = await self.session.execute(
            select(
                PathReviewModel.id.label("event_id"),
                PathReviewModel.created_by.label("actor"),
                PathReviewModel.created_at.label("created_at"),
                PathReviewModel.path_id.label("target_id"),
                literal("path").label("target_type"),
                literal("path_review").label("event_type"),
            )
            .where(PathReviewModel.created_by.in_(members_select))
            .where(PathReviewModel.created_at.is_not(None))
            .order_by(PathReviewModel.created_at.desc(), PathReviewModel.id.desc())
            .limit(int(limit))
        )

        article_review_rows = await self.session.execute(
            select(
                ArticleReviewModel.id.label("event_id"),
                ArticleReviewModel.created_by.label("actor"),
                ArticleReviewModel.created_at.label("created_at"),
                ArticleReviewModel.article_id.label("target_id"),
                literal("article").label("target_type"),
                literal("article_review").label("event_type"),
            )
            .where(ArticleReviewModel.created_by.in_(members_select))
            .where(ArticleReviewModel.created_at.is_not(None))
            .order_by(ArticleReviewModel.created_at.desc(), ArticleReviewModel.id.desc())
            .limit(int(limit))
        )

        video_review_rows = await self.session.execute(
            select(
                VideoReviewModel.id.label("event_id"),
                VideoReviewModel.created_by.label("actor"),
                VideoReviewModel.created_at.label("created_at"),
                VideoReviewModel.video_id.label("target_id"),
                literal("video").label("target_type"),
                literal("video_review").label("event_type"),
            )
            .where(VideoReviewModel.created_by.in_(members_select))
            .where(VideoReviewModel.created_at.is_not(None))
            .order_by(VideoReviewModel.created_at.desc(), VideoReviewModel.id.desc())
            .limit(int(limit))
        )

        all_rows = [
            *course_share_rows.mappings().all(),
            *article_share_rows.mappings().all(),
            *video_share_rows.mappings().all(),
            *course_review_rows.mappings().all(),
            *path_review_rows.mappings().all(),
            *article_review_rows.mappings().all(),
            *video_review_rows.mappings().all(),
        ]
        payload_rows = [
            {
                "event_id": f"{str(row.get('event_type') or '')}:{int(row.get('event_id') or 0)}",
                "event_type": str(row.get("event_type") or ""),
                "actor": str(row.get("actor") or ""),
                "created_at": self._as_iso_or_empty(row.get("created_at")),
                "target_type": str(row.get("target_type") or ""),
                "target_id": int(row.get("target_id") or 0),
                "target_label": str(row.get("target_label") or "").strip(),
            }
            for row in all_rows
            if str(row.get("actor") or "").strip() and int(row.get("target_id") or 0) > 0
        ]
        payload_rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
        return payload_rows[: int(limit)]

    async def set_team_updated_at(self, *, team_id: int, updated_at: str | datetime) -> None:
        """Touch team updated_at."""
        await self.session.execute(
            update(TeamModel).where(TeamModel.id == int(team_id)).values(updated_at=self._as_datetime(updated_at))
        )

    async def list_team_user_ids(self, *, team_id: int) -> list[str]:
        """Return usernames for one team."""
        result = await self.session.execute(select(TeamMemberModel.user_id).where(TeamMemberModel.team_id == int(team_id)))
        return [str(row[0] or "") for row in result.all()]

    async def list_workspace_user_ids(self, *, user_id: str) -> list[str]:
        """Return distinct usernames across every team the user belongs to."""
        membership_team_ids = select(TeamMemberModel.team_id).where(
            func.lower(TeamMemberModel.user_id) == func.lower(str(user_id))
        )
        result = await self.session.execute(
            select(TeamMemberModel.user_id)
            .where(TeamMemberModel.team_id.in_(membership_team_ids))
            .distinct()
            .order_by(func.lower(TeamMemberModel.user_id).asc())
        )
        return [str(row[0] or "") for row in result.all() if str(row[0] or "").strip()]
