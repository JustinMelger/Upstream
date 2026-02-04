from pathlib import Path

from fastapi import FastAPI

from backend.api import auth, courses, paths, tracking
from backend.core.config import settings
from backend.database.db import init_db, seed_courses_from_csv


app = FastAPI(title=settings.api_title, version=settings.api_version)

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


@app.on_event("startup")
def on_startup():
    """Initialize database and seed data on startup."""
    init_db()
    seed_courses_from_csv(Path(settings.courses_csv))
