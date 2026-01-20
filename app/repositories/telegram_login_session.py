from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.models.collections import TELEGRAM_LOGIN_SESSIONS_COLLECTION


class TelegramLoginSessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[TELEGRAM_LOGIN_SESSIONS_COLLECTION]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("expires_at", 1)],
            expireAfterSeconds=0,
        )

    async def create_session(self, payload: dict[str, Any]) -> None:
        await self._collection.insert_one(payload)

    async def get_by_id(self, login_token: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"_id": login_token})

    async def consume_if_approved(
        self,
        login_token: str,
    ) -> dict[str, Any] | None:
        return await self._collection.find_one_and_update(
            {"_id": login_token, "status": "APPROVED", "consumed": False},
            {"$set": {"consumed": True}},
            return_document=ReturnDocument.AFTER,
        )

    async def update_by_token(
        self,
        login_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        await self._collection.update_one(
            {"_id": login_token},
            {"$set": payload},
        )
        return await self.get_by_id(login_token)
