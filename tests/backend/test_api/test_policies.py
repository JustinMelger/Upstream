from __future__ import annotations

from fastapi import HTTPException
import pytest

from backend.api.policies import (
    require_existing_owner_or_admin,
    require_owner_or_admin,
    require_row_exists,
    require_row_parent_match,
)


pytestmark = pytest.mark.anyio


class _Auth:
    def __init__(self, *, is_admin: bool):
        self._is_admin = bool(is_admin)

    async def is_admin(self, _username: str) -> bool:
        return self._is_admin


@pytest.mark.unit
def test_require_row_exists_behaviour() -> None:
    row = {"id": 1}
    assert require_row_exists(row) == row
    with pytest.raises(HTTPException) as excinfo:
        require_row_exists(None)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "not_found"


@pytest.mark.unit
def test_require_row_parent_match_behaviour() -> None:
    require_row_parent_match(row={"course_id": 5}, parent_field="course_id", parent_id=5)
    with pytest.raises(HTTPException) as excinfo:
        require_row_parent_match(row={"course_id": 4}, parent_field="course_id", parent_id=5)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "not_found"


@pytest.mark.unit
async def test_require_owner_or_admin_behaviour() -> None:
    row = {"created_by": "alice"}

    await require_owner_or_admin(row=row, current_user="alice", auth=_Auth(is_admin=False))
    await require_owner_or_admin(row=row, current_user="bob", auth=_Auth(is_admin=True))

    with pytest.raises(HTTPException) as excinfo:
        await require_owner_or_admin(row=row, current_user="bob", auth=_Auth(is_admin=False))
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "forbidden"


@pytest.mark.unit
async def test_require_existing_owner_or_admin_behaviour() -> None:
    row = {"created_by": "alice"}
    out = await require_existing_owner_or_admin(row=row, current_user="alice", auth=_Auth(is_admin=False))
    assert out == row

    with pytest.raises(HTTPException) as missing_exc:
        await require_existing_owner_or_admin(row=None, current_user="alice", auth=_Auth(is_admin=False))
    assert missing_exc.value.status_code == 404

    with pytest.raises(HTTPException) as forbidden_exc:
        await require_existing_owner_or_admin(row=row, current_user="bob", auth=_Auth(is_admin=False))
    assert forbidden_exc.value.status_code == 403
