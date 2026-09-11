"""Seed representative browser-test data only into an explicitly disposable database."""

from __future__ import annotations

import asyncio
import os

from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.paths import PathsRepository
from backend.database.async_repositories.tracking import TrackingRepository
from backend.database.async_repositories.user_paths import UserPathsRepository
from backend.database.async_repositories.videos import VideosRepository
from backend.database.session import get_sessionmaker
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService
from backend.services.courses_service import CoursesService
from backend.services.paths_service import PathsService
from backend.services.tracking_service import TrackingService
from backend.services.user_paths_service import UserPathsService
from backend.services.videos_service import VideosService


async def seed() -> None:
    """Populate isolated preview data without touching a normal application database."""
    database_url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("E2E_DATABASE_IS_DISPOSABLE") != "1" or not database_url.rsplit("/", 1)[-1].endswith("_test"):
        raise SystemExit("Seeding requires E2E_DATABASE_IS_DISPOSABLE=1 and a database name ending in _test")
    async with get_sessionmaker()() as session, session.begin():
        auth = AuthService(AuthRepository(session))
        if await auth.has_users():
            raise SystemExit("Seed expects an empty disposable database; refusing to overwrite existing users")
        for name, password, role in [
            ("admin", "admin", "admin"),
            ("alex", "learn-demo-123", "user"),
            ("maya", "learn-demo-123", "user"),
            ("sam", "learn-demo-123", "user"),
        ]:
            await auth.create_user(name, password, role)
        courses = CoursesService(CoursesRepository(session))
        specs = [
            (
                "Production-ready Python",
                "Build reliable Python services with practical patterns for testing, packaging, and deployment.",
                "Real Python",
                "Engineering",
                "Intermediate",
                6,
                "maya",
            ),
            (
                "Designing better APIs",
                "Learn to design clear contracts, handle failures gracefully, and make APIs a pleasure to use.",
                "API Academy",
                "Engineering",
                "Intermediate",
                3,
                "sam",
            ),
            (
                "The foundations of accessible design",
                "Make interfaces that work for more people. Start with semantics, focus, and thoughtful interaction.",
                "Web.dev",
                "Design",
                "Beginner",
                2,
                "alex",
            ),
            (
                "A practical guide to PostgreSQL",
                "Understand indexes, query plans, and transactions through hands-on examples.",
                "PostgreSQL",
                "Data",
                "Intermediate",
                5,
                "maya",
            ),
        ]
        created = []
        for title, description, provider, category, level, duration, author in specs:
            created.append(
                await courses.create_course(
                    {
                        "title": title,
                        "description": description,
                        "provider": provider,
                        "category": category,
                        "level": level,
                        "duration_hours": duration,
                        "url": "https://example.com/learn/" + str(len(created)),
                        "created_by": author,
                        "recommendation_note": "A practical starting point with examples you can bring into your everyday work.",
                    }
                )
            )
        article = await ArticlesService(ArticlesRepository(session)).create_article(
            payload={
                "title": "The craft of a useful code review",
                "url": "https://example.com/code-review",
                "tags": "Engineering, collaboration",
                "recommendation_note": "This changed how I write review feedback: start with intent, then make your suggestion concrete.",
            },
            created_by="sam",
        )
        video = await VideosService(VideosRepository(session)).create_video(
            payload={
                "title": "Architecture is a series of trade-offs",
                "url": "https://example.com/architecture",
                "description": "A thoughtful conversation about making technical decisions when there is no perfect answer.",
                "provider": "Engineering talks",
                "category": "Engineering",
                "recommendation_note": "Worth watching before your next design discussion.",
            },
            created_by="maya",
        )
        path = await PathsService(PathsRepository(session)).create_path(
            {
                "name": "Build services with confidence",
                "description": "A focused path from everyday Python to reliable APIs. Read, watch, then put it into practice.",
                "created_by": "alex",
                "recommendation_note": "Follow the order, but take your time. Each resource brings a different perspective.",
                "items": [
                    {"type": "course", "id": created[0]["id"]},
                    {"type": "article", "id": article["id"]},
                    {"type": "video", "id": video["id"]},
                    {"type": "course", "id": created[1]["id"]},
                ],
            }
        )
        await UserPathsService(UserPathsRepository(session)).add_user_path("alex", path["id"])
        tracking = TrackingService(TrackingRepository(session))
        await tracking.upsert_tracking("alex", created[0]["id"], "in_progress")
        await tracking.upsert_tracking("alex", created[2]["id"], "completed")
        await tracking.upsert_tracking("alex", created[3]["id"], "interested")


if __name__ == "__main__":
    asyncio.run(seed())
