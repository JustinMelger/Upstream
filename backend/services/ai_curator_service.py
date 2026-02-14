"""AI curation service (draft planning only).

This service is intentionally deterministic and offline.
It does not call external APIs and does not write to the database.

Later, this can be replaced with a real AI+search pipeline which proposes
courses and paths that the user can review and approve.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DraftCourse:
    """Draft course suggestion.

    Attributes:
        title: Course title.
        description: Short description for search and curation.
        provider: Provider/source label.
        category: Category label.
        level: Difficulty level label.
        duration_hours: Optional estimated duration in hours.
        url: Optional URL to the resource.
    """

    title: str
    description: str
    provider: str
    category: str
    level: str
    duration_hours: float | None
    url: str


@dataclass(frozen=True, slots=True)
class DraftPath:
    """Draft path suggestion.

    Attributes:
        name: Path name.
        description: Short path description.
    """

    name: str
    description: str


class AiCuratorService:
    """Generate draft learning plans from a user goal."""

    def plan(self, *, goal: str) -> tuple[DraftPath, list[DraftCourse]]:
        """Generate a draft path and ordered draft courses.

        Args:
            goal: Free-form user goal (e.g. "build an API in Python").

        Returns:
            Tuple of `(draft_path, draft_courses)` where draft_courses order is
            the suggested learning order.
        """
        g = (goal or "").strip()
        gl = g.lower()

        # Dummy response for demo
        if "api" in gl or "rest" in gl:
            return (
                DraftPath(
                    name="Build an API (Foundations)",
                    description="A practical starter path for building a web API: HTTP basics, REST design, FastAPI, persistence, and testing.",
                ),
                [
                    DraftCourse(
                        title="HTTP overview (requests, responses, status codes)",
                        description="Fundamentals of HTTP: methods, headers, status codes, and how clients/servers communicate.",
                        provider="MDN",
                        category="Web",
                        level="Beginner",
                        duration_hours=1.5,
                        url="https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview",
                    ),
                    DraftCourse(
                        title="REST API design basics",
                        description="Core REST concepts and practical API design guidelines for resources, errors, and versioning.",
                        provider="Microsoft Learn",
                        category="Architecture",
                        level="Beginner",
                        duration_hours=1.0,
                        url="https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design",
                    ),
                    DraftCourse(
                        title="FastAPI tutorial",
                        description="Build a production-ready API with FastAPI: routing, dependencies, models, and async endpoints.",
                        provider="FastAPI Docs",
                        category="Backend",
                        level="Intermediate",
                        duration_hours=3.0,
                        url="https://fastapi.tiangolo.com/tutorial/",
                    ),
                    DraftCourse(
                        title="SQLAlchemy 2.0 tutorial (ORM basics)",
                        description="Learn SQLAlchemy 2.0 ORM fundamentals: sessions, models, queries, and transactions.",
                        provider="SQLAlchemy Docs",
                        category="Database",
                        level="Intermediate",
                        duration_hours=3.0,
                        url="https://docs.sqlalchemy.org/en/20/tutorial/",
                    ),
                    DraftCourse(
                        title="Testing FastAPI apps",
                        description="Test FastAPI applications with pytest and httpx; cover dependencies and async endpoints.",
                        provider="FastAPI Docs",
                        category="Testing",
                        level="Intermediate",
                        duration_hours=1.5,
                        url="https://fastapi.tiangolo.com/tutorial/testing/",
                    ),
                ],
            )

        # Default: generic "learning path" placeholder.
        return (
            DraftPath(
                name="Learning Plan (Draft)",
                description=f"Draft learning plan for: {g or '(no goal provided)'}",
            ),
            [
                DraftCourse(
                    title="Define requirements and success criteria",
                    description="Turn your goal into concrete requirements, milestones, and acceptance criteria.",
                    provider="Learning Hub",
                    category="Planning",
                    level="Beginner",
                    duration_hours=None,
                    url="",
                ),
                DraftCourse(
                    title="Pick an implementation stack and build a small prototype",
                    description="Choose tools and frameworks, then validate them by building a small end-to-end prototype.",
                    provider="Learning Hub",
                    category="Planning",
                    level="Beginner",
                    duration_hours=None,
                    url="",
                ),
            ],
        )
