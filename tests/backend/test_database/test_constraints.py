import pytest
from sqlalchemy import text


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_migrations_create_expected_foreign_keys(db_session):
    """Alembic migrations create expected foreign key constraints."""
    rows = await db_session.execute(
        text(
            "SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column "
            "FROM information_schema.table_constraints AS tc "
            "JOIN information_schema.key_column_usage AS kcu "
            "  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
            "JOIN information_schema.constraint_column_usage AS ccu "
            "  ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema "
            "WHERE tc.table_schema = 'public' "
            "  AND tc.constraint_type = 'FOREIGN KEY' "
            "ORDER BY tc.table_name, kcu.column_name"
        )
    )
    fks = {(str(r.table_name), str(r.column_name), str(r.foreign_table), str(r.foreign_column)) for r in rows.mappings().all()}

    assert ("tracking", "course_id", "courses", "id") in fks
    assert ("path_courses", "course_id", "courses", "id") in fks
    assert ("sessions", "colleague_id", "users", "username") in fks


@pytest.mark.unit
async def test_migrations_enforce_unique_session_token_hash(db_session):
    """Session token hashes are unique at the database level."""
    rows = await db_session.execute(
        text(
            "SELECT kcu.table_name, kcu.column_name "
            "FROM information_schema.table_constraints AS tc "
            "JOIN information_schema.key_column_usage AS kcu "
            "  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
            "WHERE tc.table_schema = 'public' "
            "  AND tc.constraint_type = 'UNIQUE' "
            "  AND kcu.table_name = 'sessions'"
        )
    )
    uniques = {(str(r.table_name), str(r.column_name)) for r in rows.mappings().all()}
    assert ("sessions", "token_hash") in uniques
