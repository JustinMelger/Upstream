from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.exc import IntegrityError


async def upsert_review_id(
    *,
    get_existing: Callable[[], Awaitable[Any]],
    create: Callable[[], Awaitable[int]],
    get_concurrent: Callable[[], Awaitable[Any]],
    update: Callable[[int], Awaitable[Any]],
) -> int:
    """Create-or-update helper with integrity-race fallback.

    Returns:
        Review id that was created or updated.
    """
    existing = await get_existing()
    if existing is not None:
        review_id = int(getattr(existing, "id", 0))
        await update(review_id)
        return review_id

    try:
        return int(await create())
    except IntegrityError:
        concurrent = await get_concurrent()
        if concurrent is None:
            raise
        review_id = int(getattr(concurrent, "id", 0))
        await update(review_id)
        return review_id
