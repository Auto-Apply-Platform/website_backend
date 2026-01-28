from app.models.collections import REQUESTS_COLLECTION
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository):
    collection_name = REQUESTS_COLLECTION

    async def get_request_by_id(self, request_id: str) -> dict | None:
        return await self.get_by_id(request_id)

    async def delete_request_by_id(self, request_id: str) -> bool:
        return await self.delete_by_id(request_id)

    async def list_requests(self, filters: dict | None = None) -> list[dict]:
        query = filters or {}
        cursor = self._collection.find(query)
        return [doc async for doc in cursor]

    async def list_status_backfill_candidates(
        self,
        allowed_statuses: list[str],
    ) -> list[dict]:
        cursor = self._collection.find(
            {
                "$or": [
                    {"on_hold": {"$exists": False}},
                    {"max_stage": {"$exists": False}},
                    {"status": {"$exists": False}},
                    {"status": {"$nin": allowed_statuses}},
                ]
            }
        )
        return [doc async for doc in cursor]
