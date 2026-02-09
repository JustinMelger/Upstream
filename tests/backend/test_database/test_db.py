import pytest
from sqlalchemy import text


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_migrations_create_expected_columns(db_session):
    """Alembic migrations create expected columns."""
    rows = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_paths'")
    )
    columns = {row[0] for row in rows.all()}
    assert "status" in columns
    assert "updated_at" in columns


@pytest.mark.unit
async def test_migrations_create_courses_table(db_session):
    """Alembic migrations create the courses table."""
    rows = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'courses'")
    )
    columns = {row[0] for row in rows.all()}
    assert "id" in columns
    assert "title" in columns
