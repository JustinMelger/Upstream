from __future__ import annotations

from typing import Callable, Literal

from pydantic import StrictInt, StrictStr, ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.notifications import NotificationsRepository
from backend.database.tx import session_scope


class NotificationsServiceError(ServiceError):
    """Domain error for notifications failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        super().__init__(detail=detail, status_code=status_code)


@dataclass
class NotificationActivityQuery:
    """Typed service-layer payload for activity feed queries."""

    current_user: StrictStr | None = None
    limit: StrictInt | None = 30
    scope: StrictStr | None = "inbox"


TargetType = Literal["course", "path", "article"]


@dataclass
class ActivityEvent:
    """Typed activity event emitted by the notifications service."""

    event_id: StrictStr
    event_type: StrictStr
    created_at: StrictStr
    actor: StrictStr
    message: StrictStr
    target_type: TargetType
    target_id: StrictInt
    target_label: StrictStr

    def to_payload(self) -> dict[str, str | int]:
        """Serialize to API response payload."""
        return {
            "event_id": str(self.event_id),
            "event_type": str(self.event_type),
            "created_at": str(self.created_at),
            "actor": str(self.actor),
            "message": str(self.message),
            "target_type": str(self.target_type),
            "target_id": int(self.target_id),
            "target_label": str(self.target_label),
        }


def notifications_error_handler(
    message: str = "An unexpected error occurred while handling notifications",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Wrap uncaught notification errors into a domain ServiceError."""
    return error_handler(
        service_error=NotificationsServiceError,
        message=message,
        status_code=status_code,
        log_message="Notifications service error",
    )


class NotificationsService:
    """Activity feed service for shared/recommended notifications."""

    def __init__(self, repo: NotificationsRepository):
        self._repo = repo

    @notifications_error_handler()
    async def list_activity(self, *, current_user: str, limit: int = 30, scope: str = "inbox") -> list[dict]:
        """Return activity rows for inbox or team timeline scope."""
        data = self._parse_activity_query(
            {
                "current_user": current_user,
                "limit": limit,
                "scope": scope,
            }
        )
        username = str(data.current_user or "").strip()
        if not username:
            raise NotificationsServiceError(detail="invalid_payload", status_code=400)
        safe_limit = max(1, min(data.limit or 30, 100))
        source_limit = max(20, safe_limit * 4)
        scope_value = str(data.scope or "inbox").strip().lower()
        if scope_value not in {"inbox", "team"}:
            raise NotificationsServiceError(detail="invalid_payload", status_code=400)
        is_team = scope_value == "team"

        async with session_scope(self._repo.session):
            course_shares = await self._repo.list_recent_course_share_events(limit=source_limit) if is_team else []
            course_recommendations = await self._repo.list_recent_course_recommendation_events(limit=source_limit)
            path_recommendations = await self._repo.list_recent_path_recommendation_events(limit=source_limit)
            course_reviews = await self._repo.list_recent_course_review_events(limit=source_limit)
            path_reviews = await self._repo.list_recent_path_review_events(limit=source_limit)
            article_reviews = await self._repo.list_recent_article_review_events(limit=source_limit)
            own_course_recommendations = (
                await self._repo.list_recent_course_recommendation_events_by_user(created_by=username, limit=safe_limit)
                if is_team
                else []
            )
            own_path_recommendations = (
                await self._repo.list_recent_path_recommendation_events_by_user(created_by=username, limit=safe_limit)
                if is_team
                else []
            )

        events: list[ActivityEvent] = []
        events.extend(self._build_course_share_events(rows=course_shares, username=username))
        events.extend(
            self._build_recommendation_events(
                rows=list(course_recommendations) + list(own_course_recommendations),
                username=username,
                is_team=is_team,
                kind="course",
            )
        )
        events.extend(
            self._build_recommendation_events(
                rows=list(path_recommendations) + list(own_path_recommendations),
                username=username,
                is_team=is_team,
                kind="path",
            )
        )
        events.extend(
            self._build_rating_events(
                rows=course_reviews,
                username=username,
                is_team=is_team,
                kind="course",
            )
        )
        events.extend(
            self._build_rating_events(
                rows=path_reviews,
                username=username,
                is_team=is_team,
                kind="path",
            )
        )
        events.extend(
            self._build_rating_events(
                rows=article_reviews,
                username=username,
                is_team=is_team,
                kind="article",
            )
        )

        return self._finalize_events(events=events, limit=safe_limit)

    @staticmethod
    def _parse_activity_query(payload: dict) -> NotificationActivityQuery:
        """Parse and validate the activity feed query payload."""
        try:
            return NotificationActivityQuery(**dict(payload or {}))
        except ValidationError as exc:
            raise NotificationsServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _build_course_share_events(*, rows: list[dict], username: str) -> list[ActivityEvent]:
        """Build course share events."""
        out: list[ActivityEvent] = []
        for row in rows:
            actor = str(row.get("created_by") or "").strip()
            if not actor:
                continue
            title = str(row.get("title") or "").strip() or "Untitled course"
            event_type = "course_shared"
            message = f'{actor} shared "{title}"'
            if actor == username:
                event_type = "you_shared_course"
                message = f'You shared "{title}"'
            out.append(
                ActivityEvent(
                    event_id=f"course_shared:{int(row.get('course_id') or 0)}",
                    event_type=event_type,
                    created_at=str(row.get("created_at") or ""),
                    actor=actor,
                    message=message,
                    target_type="course",
                    target_id=int(row.get("course_id") or 0),
                    target_label=title,
                )
            )
        return out

    @staticmethod
    def _build_recommendation_events(
        *, rows: list[dict], username: str, is_team: bool, kind: Literal["course", "path"]
    ) -> list[ActivityEvent]:
        """Build course/path recommendation events."""
        key = kind
        owner_key = "course_owner" if key == "course" else "path_owner"
        id_key = "course_id" if key == "course" else "path_id"
        label_key = "title" if key == "course" else "name"
        out: list[ActivityEvent] = []
        for row in rows:
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get(owner_key) or "").strip()
            if not actor:
                continue
            label = str(row.get(label_key) or "").strip() or f"Untitled {key}"
            if is_team:
                event_type = f"{key}_recommended"
                message = f'{actor} recommended "{label}"'
                if actor == username:
                    event_type = f"you_recommended_{key}"
                    message = f'You recommended "{label}"'
                elif owner and owner == username:
                    event_type = f"your_{key}_recommended"
                    message = f'{actor} recommended your shared {key} "{label}"'
            else:
                if actor == username or owner != username:
                    continue
                event_type = f"your_{key}_recommended"
                message = f'{actor} recommended your shared {key} "{label}"'
            out.append(
                ActivityEvent(
                    event_id=f"{key}_recommended:{int(row.get('recommendation_id') or 0)}",
                    event_type=event_type,
                    created_at=str(row.get("created_at") or ""),
                    actor=actor,
                    message=message,
                    target_type=key,
                    target_id=int(row.get(id_key) or 0),
                    target_label=label,
                )
            )
        return out

    @staticmethod
    def _build_rating_events(
        *, rows: list[dict], username: str, is_team: bool, kind: Literal["course", "path", "article"]
    ) -> list[ActivityEvent]:
        """Build course/path/article rating events."""
        owner_key = {
            "course": "course_owner",
            "path": "path_owner",
            "article": "article_owner",
        }[kind]
        id_key = {
            "course": "course_id",
            "path": "path_id",
            "article": "article_id",
        }[kind]
        label_key = {
            "course": "title",
            "path": "name",
            "article": "title",
        }[kind]
        out: list[ActivityEvent] = []
        for row in rows:
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get(owner_key) or "").strip()
            if not actor:
                continue
            label = str(row.get(label_key) or "").strip() or f"Untitled {kind}"
            rating = int(row.get("rating") or 0)
            stars = f"{rating}/5" if rating > 0 else "a rating"
            if is_team:
                event_type = f"{kind}_rated"
                message = f'{actor} rated "{label}" ({stars})'
                if actor == username:
                    event_type = f"you_rated_{kind}"
                    message = f'You rated "{label}" ({stars})'
                elif owner and owner == username:
                    event_type = f"your_{kind}_rated"
                    message = f'{actor} rated your shared {kind} "{label}" ({stars})'
            else:
                if actor == username or owner != username:
                    continue
                event_type = f"your_{kind}_rated"
                message = f'{actor} rated your shared {kind} "{label}" ({stars})'
            out.append(
                ActivityEvent(
                    event_id=f"{kind}_rated:{int(row.get('review_id') or 0)}",
                    event_type=event_type,
                    created_at=str(row.get("created_at") or ""),
                    actor=actor,
                    message=message,
                    target_type=kind,
                    target_id=int(row.get(id_key) or 0),
                    target_label=label,
                )
            )
        return out

    @staticmethod
    def _finalize_events(*, events: list[ActivityEvent], limit: int) -> list[dict]:
        """Normalize, dedupe, sort, and limit event rows."""
        filtered = [e for e in events if int(e.target_id) > 0 and str(e.created_at).strip()]
        deduped: dict[str, ActivityEvent] = {}
        for row in filtered:
            deduped[str(row.event_id or "")] = row
        out = [row for row in deduped.values() if str(row.event_id or "").strip()]
        out.sort(key=lambda row: (str(row.created_at or ""), str(row.event_id or "")), reverse=True)
        return [row.to_payload() for row in out[: max(1, int(limit or 1))]]
