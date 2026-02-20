from __future__ import annotations

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, ServiceError
from backend.database.async_repositories.notifications import NotificationsRepository
from backend.database.tx import session_scope


class NotificationsServiceError(ServiceError):
    """Domain error for notifications failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        super().__init__(detail=detail, status_code=status_code)


@dataclass
class NotificationActivityQuery:
    """Typed service-layer payload for activity feed queries."""

    current_user: str | None = None
    limit: int | str | None = 30
    scope: str | None = "inbox"


def notifications_error_handler(
    message: str = "An unexpected error occurred while handling notifications",
    status_code: int = 500,
):
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
        safe_limit = max(1, min(int(data.limit or 30), 100))
        source_limit = max(20, safe_limit * 4)
        scope_value = str(data.scope or "inbox").strip().lower()
        if scope_value not in {"inbox", "team"}:
            scope_value = "inbox"
        is_team = scope_value == "team"

        async with session_scope(self._repo.session):
            course_shares = await self._repo.list_recent_course_share_events(limit=source_limit) if is_team else []
            course_recommendations = await self._repo.list_recent_course_recommendation_events(limit=source_limit)
            path_recommendations = await self._repo.list_recent_path_recommendation_events(limit=source_limit)
            course_reviews = await self._repo.list_recent_course_review_events(limit=source_limit)
            path_reviews = await self._repo.list_recent_path_review_events(limit=source_limit)
            article_reviews = await self._repo.list_recent_article_review_events(limit=source_limit)
            own_course_recommendations = (
                await self._repo.list_recent_course_recommendation_events_by_user(
                    created_by=str(current_user), limit=safe_limit
                )
                if is_team
                else []
            )
            own_path_recommendations = (
                await self._repo.list_recent_path_recommendation_events_by_user(created_by=str(current_user), limit=safe_limit)
                if is_team
                else []
            )

        events: list[dict] = []

        for row in course_shares:
            actor = str(row.get("created_by") or "").strip()
            if not actor:
                continue
            title = str(row.get("title") or "").strip() or "Untitled course"
            event_type = "course_shared"
            message = f'{actor} shared "{title}"'
            if actor == username:
                event_type = "you_shared_course"
                message = f'You shared "{title}"'
            events.append(
                {
                    "event_id": f"course_shared:{int(row.get('course_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "course",
                    "target_id": int(row.get("course_id") or 0),
                    "target_label": title,
                }
            )

        for row in list(course_recommendations) + list(own_course_recommendations):
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get("course_owner") or "").strip()
            if not actor:
                continue
            title = str(row.get("title") or "").strip() or "Untitled course"
            if is_team:
                event_type = "course_recommended"
                message = f'{actor} recommended "{title}"'
                if actor == username:
                    event_type = "you_recommended_course"
                    message = f'You recommended "{title}"'
                elif owner and owner == username:
                    event_type = "your_course_recommended"
                    message = f'{actor} recommended your shared course "{title}"'
            else:
                if actor == username or owner != username:
                    continue
                event_type = "your_course_recommended"
                message = f'{actor} recommended your shared course "{title}"'
            events.append(
                {
                    "event_id": f"course_recommended:{int(row.get('recommendation_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "course",
                    "target_id": int(row.get("course_id") or 0),
                    "target_label": title,
                }
            )

        for row in list(path_recommendations) + list(own_path_recommendations):
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get("path_owner") or "").strip()
            if not actor:
                continue
            name = str(row.get("name") or "").strip() or "Untitled path"
            if is_team:
                event_type = "path_recommended"
                message = f'{actor} recommended "{name}"'
                if actor == username:
                    event_type = "you_recommended_path"
                    message = f'You recommended "{name}"'
                elif owner and owner == username:
                    event_type = "your_path_recommended"
                    message = f'{actor} recommended your shared path "{name}"'
            else:
                if actor == username or owner != username:
                    continue
                event_type = "your_path_recommended"
                message = f'{actor} recommended your shared path "{name}"'
            events.append(
                {
                    "event_id": f"path_recommended:{int(row.get('recommendation_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "path",
                    "target_id": int(row.get("path_id") or 0),
                    "target_label": name,
                }
            )

        for row in course_reviews:
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get("course_owner") or "").strip()
            if not actor:
                continue
            title = str(row.get("title") or "").strip() or "Untitled course"
            rating = int(row.get("rating") or 0)
            stars = f"{rating}/5" if rating > 0 else "a rating"
            if is_team:
                event_type = "course_rated"
                message = f'{actor} rated "{title}" ({stars})'
                if actor == username:
                    event_type = "you_rated_course"
                    message = f'You rated "{title}" ({stars})'
                elif owner and owner == username:
                    event_type = "your_course_rated"
                    message = f'{actor} rated your shared course "{title}" ({stars})'
            else:
                if actor == username or owner != username:
                    continue
                event_type = "your_course_rated"
                message = f'{actor} rated your shared course "{title}" ({stars})'
            events.append(
                {
                    "event_id": f"course_rated:{int(row.get('review_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "course",
                    "target_id": int(row.get("course_id") or 0),
                    "target_label": title,
                }
            )

        for row in path_reviews:
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get("path_owner") or "").strip()
            if not actor:
                continue
            name = str(row.get("name") or "").strip() or "Untitled path"
            rating = int(row.get("rating") or 0)
            stars = f"{rating}/5" if rating > 0 else "a rating"
            if is_team:
                event_type = "path_rated"
                message = f'{actor} rated "{name}" ({stars})'
                if actor == username:
                    event_type = "you_rated_path"
                    message = f'You rated "{name}" ({stars})'
                elif owner and owner == username:
                    event_type = "your_path_rated"
                    message = f'{actor} rated your shared path "{name}" ({stars})'
            else:
                if actor == username or owner != username:
                    continue
                event_type = "your_path_rated"
                message = f'{actor} rated your shared path "{name}" ({stars})'
            events.append(
                {
                    "event_id": f"path_rated:{int(row.get('review_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "path",
                    "target_id": int(row.get("path_id") or 0),
                    "target_label": name,
                }
            )

        for row in article_reviews:
            actor = str(row.get("created_by") or "").strip()
            owner = str(row.get("article_owner") or "").strip()
            if not actor:
                continue
            title = str(row.get("title") or "").strip() or "Untitled article"
            rating = int(row.get("rating") or 0)
            stars = f"{rating}/5" if rating > 0 else "a rating"
            if is_team:
                event_type = "article_rated"
                message = f'{actor} rated "{title}" ({stars})'
                if actor == username:
                    event_type = "you_rated_article"
                    message = f'You rated "{title}" ({stars})'
                elif owner and owner == username:
                    event_type = "your_article_rated"
                    message = f'{actor} rated your shared article "{title}" ({stars})'
            else:
                if actor == username or owner != username:
                    continue
                event_type = "your_article_rated"
                message = f'{actor} rated your shared article "{title}" ({stars})'
            events.append(
                {
                    "event_id": f"article_rated:{int(row.get('review_id') or 0)}",
                    "event_type": event_type,
                    "created_at": str(row.get("created_at") or ""),
                    "actor": actor,
                    "message": message,
                    "target_type": "article",
                    "target_id": int(row.get("article_id") or 0),
                    "target_label": title,
                }
            )

        events = [e for e in events if int(e.get("target_id") or 0) > 0 and str(e.get("created_at") or "").strip()]
        deduped: dict[str, dict] = {}
        for row in events:
            deduped[str(row.get("event_id") or "")] = row
        events = [row for row in deduped.values() if str(row.get("event_id") or "").strip()]
        events.sort(key=lambda row: (str(row.get("created_at") or ""), str(row.get("event_id") or "")), reverse=True)
        return events[:safe_limit]

    @staticmethod
    def _parse_activity_query(payload: dict) -> NotificationActivityQuery:
        """Parse and validate the activity feed query payload."""
        try:
            return NotificationActivityQuery(**dict(payload or {}))
        except ValidationError as exc:
            raise NotificationsServiceError(detail="invalid_payload", status_code=400) from exc
