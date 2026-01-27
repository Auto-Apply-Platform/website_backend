from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.request import RequestRepository
from app.utils.mongo import serialize_document


async def list_requests(
    db: AsyncIOMotorDatabase,
    *,
    role: str | None = None,
    grade: str | None = None,
    has_deadline: bool | None = None,
) -> list[dict]:
    repo = RequestRepository(db)
    filters: dict[str, object] = {}
    if role:
        filters["vacancy.role"] = role
    if grade:
        filters["vacancy.grade"] = grade
    if has_deadline is True:
        filters["vacancy.application_deadline"] = {"$exists": True, "$ne": ""}
    elif has_deadline is False:
        filters["$or"] = [
            {"vacancy.application_deadline": {"$exists": False}},
            {"vacancy.application_deadline": ""},
            {"vacancy.application_deadline": None},
        ]

    docs = await repo.list_requests(filters=filters)
    return [serialize_document(doc) for doc in docs]
