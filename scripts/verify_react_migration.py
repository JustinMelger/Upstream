"""Verify the React migration preserves populated legacy data in an empty test database."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


TABLES = (
    "users",
    "courses",
    "articles",
    "videos",
    "paths",
    "path_items",
    "course_reviews",
    "article_reviews",
    "video_reviews",
    "path_reviews",
    "tracking",
    "user_paths",
    "teams",
    "team_members",
)


async def assert_empty() -> None:
    """Refuse to migrate any database that already contains tables."""
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.connect() as conn:
        count = await conn.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"))
        if count:
            raise SystemExit("Migration verification requires an empty disposable database")
    await engine.dispose()


async def seed_legacy() -> dict:
    """Write a populated legacy fixture and retain all original field values."""
    statements = [
        "INSERT INTO users(username,password_hash,role,created_at,updated_at,disabled) VALUES ('legacy','test-hash','user',now(),now(),false)",
        "INSERT INTO courses(id,title,description,created_by,created_at) VALUES (1,'Legacy course','Keep this description','legacy',now())",
        "INSERT INTO articles(id,title,url,created_by,created_at) VALUES (1,'Legacy article','https://example.com/article','legacy',now())",
        "INSERT INTO videos(id,title,description,url,created_by,created_at) VALUES (1,'Legacy video','Keep video','https://example.com/video','legacy',now())",
        "INSERT INTO paths(id,name,description,created_by) VALUES (1,'Legacy path','Keep this path','legacy')",
        "INSERT INTO path_items(path_id,item_type,item_id,position) VALUES (1,'video',1,0),(1,'course',1,1),(1,'article',1,2)",
        "INSERT INTO course_reviews(course_id,rating,text,created_by,created_at) VALUES (1,4,'Keep review','legacy',now())",
        "INSERT INTO article_reviews(article_id,rating,text,created_by,created_at) VALUES (1,4,'Keep review','legacy',now())",
        "INSERT INTO video_reviews(video_id,rating,text,created_by,created_at) VALUES (1,4,'Keep review','legacy',now())",
        "INSERT INTO path_reviews(path_id,rating,text,created_by,created_at) VALUES (1,4,'Keep review','legacy',now())",
        "INSERT INTO tracking(colleague_id,course_id,status,updated_at) VALUES ('legacy',1,'completed',now())",
        "INSERT INTO user_paths(colleague_id,path_id,status,created_at) VALUES ('legacy',1,'in_progress',now())",
        "INSERT INTO teams(id,name,description,owner_user_id,created_at,updated_at) VALUES (1,'Legacy team','Keep for rollback','legacy',now(),now())",
        "INSERT INTO team_members(team_id,user_id,role,created_at,updated_at) VALUES (1,'legacy','owner',now(),now())",
    ]
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        for statement in statements:
            await conn.execute(text(statement))
        snapshots = {
            table: [dict(row) for row in (await conn.execute(text(f'SELECT * FROM "{table}"'))).mappings()] for table in TABLES
        }
    await engine.dispose()
    return snapshots


async def verify(snapshots: dict) -> None:
    """Compare every original field and verify additive metadata semantics."""
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.connect() as conn:
        for table, before in snapshots.items():
            after = [dict(row) for row in (await conn.execute(text(f'SELECT * FROM "{table}"'))).mappings()]
            assert len(after) == len(before), table
            original_columns = list(before[0])
            assert [{key: row[key] for key in original_columns} for row in after] == before, table
        for table in ("courses", "articles", "videos", "paths"):
            assert await conn.scalar(text(f'SELECT recommendation_note FROM "{table}" WHERE id=1')) is None
        assert await conn.scalar(text("SELECT created_at FROM paths WHERE id=1")) is None
        assert await conn.scalar(text("SELECT description FROM articles WHERE id=1")) is None
    await engine.dispose()


def main() -> None:
    """Exercise upgrade on populated data, separate from the application database."""
    url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("E2E_DATABASE_IS_DISPOSABLE") != "1" or not url.rsplit("/", 1)[-1].endswith("_test"):
        raise SystemExit("Set E2E_DATABASE_IS_DISPOSABLE=1 and use a database ending in _test")
    asyncio.run(assert_empty())
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "20260318_0017"], check=True)
    snapshots = asyncio.run(seed_legacy())
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    asyncio.run(verify(snapshots))
    print("Populated legacy migration: all original records preserved; notes and path timestamps remain null.")


if __name__ == "__main__":
    main()
