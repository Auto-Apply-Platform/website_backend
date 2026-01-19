from typing import Any

from app.models.collections import USERS_COLLECTION
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    collection_name = USERS_COLLECTION

    async def get_by_username(self, username: str) -> dict[str, Any] | None:
        document = await self._collection.find_one({"username": username})
        return document
