import pytest

from backend.database import db as db_module


@pytest.mark.unit
def test_transaction_rolls_back_on_error(app_client):
    """SQLiteDatabase.transaction rolls back changes when an exception is raised."""
    db_module.init_db()

    try:
        with db_module.database.transaction() as conn:
            conn.execute("INSERT INTO paths (name, description) VALUES (?, ?)", ("TxTest", "desc"))
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    with db_module.get_conn() as conn:
        row = conn.execute("SELECT 1 FROM paths WHERE name = ?", ("TxTest",)).fetchone()
    assert row is None
