from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.mongo import serialize_document


class BaseRepository:
    collection_name: str

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self.collection_name]

    async def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(payload)
        document = await self._collection.find_one({"_id": result.inserted_id})
        if document:
            return serialize_document(document)
        return {"id": str(result.inserted_id)}

    async def get_by_id(self, item_id: str) -> dict[str, Any] | None:
        document = await self._collection.find_one({"_id": ObjectId(item_id)})
        return serialize_document(document) if document else None

    async def update_by_id(
        self,
        item_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not payload:
            return await self.get_by_id(item_id)
        await self._collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": payload},
        )
        return await self.get_by_id(item_id)

    async def delete_by_id(self, item_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(item_id)})
        return result.deleted_count == 1

    async def list(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self._collection.find().limit(limit)
        return [serialize_document(doc) async for doc in cursor]
