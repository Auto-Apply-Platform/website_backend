from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.request import RequestRepository
from app.utils.mongo import serialize_document


async def list_requests(db: AsyncIOMotorDatabase) -> list[dict]:
    repo = RequestRepository(db)
    docs = await repo.list_requests()
    return [serialize_document(doc) for doc in docs]
