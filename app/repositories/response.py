from app.models.collections import RESPONSES_COLLECTION
from app.repositories.base import BaseRepository


class ResponseRepository(BaseRepository):
    collection_name = RESPONSES_COLLECTION

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("request_id", 1), ("developer_id", 1)],
            unique=True,
            name="uniq_response_request_developer",
        )

    async def get_by_request_developer(
        self,
        request_id: str,
        developer_id: str,
        *,
        session=None,
    ) -> dict | None:
        return await self._collection.find_one(
            {"request_id": request_id, "developer_id": developer_id},
            session=session,
        )
