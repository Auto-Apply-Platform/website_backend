from app.models.collections import REQUESTS_COLLECTION
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository):
    collection_name = REQUESTS_COLLECTION

    async def list_requests(self) -> list[dict]:
        cursor = self._collection.find({}).sort("created_at", -1)
        return [doc async for doc in cursor]
