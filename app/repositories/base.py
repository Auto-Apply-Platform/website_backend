from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.mongo import serialize_document


class BaseRepository:
    collection_name: str

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self.collection_name]

    async def create(
        self,
        payload: dict[str, Any],
        *,
        session: Any | None = None,
    ) -> dict[str, Any]:
        result = await self._collection.insert_one(payload, session=session)
        document = await self._collection.find_one(
            {"_id": result.inserted_id},
            session=session,
        )
        if document:
            return serialize_document(document)
        return {"id": str(result.inserted_id)}

    async def get_by_id(
        self,
        item_id: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        document = await self._collection.find_one(
            {"_id": ObjectId(item_id)},
            session=session,
        )
        return serialize_document(document) if document else None

    async def update_by_id(
        self,
        item_id: str,
        payload: dict[str, Any],
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        if not payload:
            return await self.get_by_id(item_id, session=session)
        await self._collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": payload},
            session=session,
        )
        return await self.get_by_id(item_id, session=session)

    async def delete_by_id(self, item_id: str, *, session: Any | None = None) -> bool:
        result = await self._collection.delete_one(
            {"_id": ObjectId(item_id)},
            session=session,
        )
        return result.deleted_count == 1

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        sort: list[tuple[str, int]] | None = None,
        filters: dict[str, Any] | None = None,
        session: Any | None = None,
    ) -> list[dict[str, Any]]:
        query = filters or {}
        cursor = self._collection.find(query, session=session).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return [serialize_document(doc) async for doc in cursor]

    async def count(
        self,
        filters: dict[str, Any] | None = None,
        *,
        session: Any | None = None,
    ) -> int:
        query = filters or {}
        return await self._collection.count_documents(query, session=session)
