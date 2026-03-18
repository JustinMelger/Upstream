from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import ProgrammingError

from backend.database.async_repositories.paths import PathsRepository


pytestmark = pytest.mark.anyio


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _MappingsResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return list(self._rows)


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _LegacySession:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return _ScalarResult(SimpleNamespace(id=7, name="Legacy Path", description="desc", created_by="alice"))
        if self.calls == 2:
            raise ProgrammingError("select", {}, Exception("path_items missing"))
        if self.calls == 3:
            return _MappingsResult([{"item_type": "course", "item_id": 101, "position": 0}])
        if self.calls == 4:
            return _RowsResult(
                [
                    SimpleNamespace(
                        id=101,
                        title="Fallback Course",
                        description="desc",
                        provider="Provider",
                        category="Backend",
                        level="Intermediate",
                        duration_hours=3.5,
                        url="https://example.com/course",
                    )
                ]
            )
        raise AssertionError("unexpected execute call")


@pytest.mark.unit
async def test_paths_repository_get_path_falls_back_to_legacy_path_courses_when_path_items_missing() -> None:
    repo = PathsRepository(_LegacySession())

    result = await repo.get_path(7)

    assert result is not None
    path, items = result
    assert path.id == 7
    assert [item.item_type for item in items] == ["course"]
    assert [item.id for item in items] == [101]
