import pytest
from sqlalchemy import text


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_transaction_rolls_back_on_error(db_session):
    """AsyncSession.begin rolls back changes when an exception is raised."""
    try:
        async with db_session.begin():
            await db_session.execute(
                text("INSERT INTO paths (name, description) VALUES (:name, :description)"),
                {"name": "TxTest", "description": "desc"},
            )
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    result = await db_session.execute(text("SELECT 1 FROM paths WHERE name = :name"), {"name": "TxTest"})
    assert result.first() is None
