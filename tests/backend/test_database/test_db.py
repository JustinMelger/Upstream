import pytest

from backend.database.db import get_conn, init_db, seed_courses_from_csv


@pytest.mark.unit
def test_init_db_creates_columns(app_client):
    """Database initialization creates expected columns."""
    init_db()
    with get_conn() as conn:
        rows = conn.execute("PRAGMA table_info(user_paths)").fetchall()
        columns = {row["name"] for row in rows}
    assert "status" in columns
    assert "updated_at" in columns


@pytest.mark.unit
def test_seed_courses_from_csv(app_client, tmp_path):
    """Seeding courses inserts rows from a CSV file."""
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM courses")
        conn.commit()

    csv_path = tmp_path / "courses.csv"
    csv_path.write_text(
        "title,provider,category,level,duration_hours,url\n"
        "Course A,Provider A,Category A,Beginner,2,http://example.com/a\n"
        "Course B,Provider B,Category B,Advanced,3,http://example.com/b\n",
        encoding="utf-8",
    )

    seed_courses_from_csv(csv_path)

    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) as count FROM courses").fetchone()
    assert row["count"] == 2
