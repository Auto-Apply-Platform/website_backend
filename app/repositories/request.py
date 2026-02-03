from app.models.collections import REQUESTS_COLLECTION
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository):
    collection_name = REQUESTS_COLLECTION

    async def get_request_by_id(self, request_id: str) -> dict | None:
        return await self.get_by_id(request_id)

    async def delete_request_by_id(self, request_id: str) -> bool:
        return await self.delete_by_id(request_id)

    async def list_requests(
        self,
        filters: dict | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict]:
        query = filters or {}
        cursor = self._collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        return [doc async for doc in cursor]
