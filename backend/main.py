from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from backend.api import auth, courses, paths, tracking
from backend.core.config import settings
from backend.database.db import init_db, seed_courses_from_csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed data on startup."""
    init_db()
    seed_courses_from_csv(Path(settings.courses_csv))
    yield


app = FastAPI(title=settings.api_title, version=settings.api_version, lifespan=lifespan)

app.include_router(courses.router)
app.include_router(paths.router)
app.include_router(tracking.router)
app.include_router(auth.router)


@app.get("/health", tags=["health"])
def health():
    """Health check endpoint.

    Returns:
        dict: Simple status payload.
    """
    return {"status": "ok"}


def on_startup():
    """Backward-compatible startup hook for tests."""
    init_db()
    seed_courses_from_csv(Path(settings.courses_csv))
