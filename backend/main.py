from fastapi import FastAPI

from pathlib import Path

from backend.core.config import settings
from backend.api import courses, paths, tracking
from backend.database.db import init_db, seed_courses_from_csv

app = FastAPI(title=settings.api_title, version=settings.api_version)

app.include_router(courses.router)
app.include_router(paths.router)
app.include_router(tracking.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    init_db()
    seed_courses_from_csv(Path(settings.courses_csv))
