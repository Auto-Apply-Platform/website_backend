from app.models.collections import REQUESTS_COLLECTION
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository):
    collection_name = REQUESTS_COLLECTION

    async def list_requests(self, filters: dict | None = None) -> list[dict]:
        query = filters or {}
        cursor = self._collection.find(query)
        return [doc async for doc in cursor]
