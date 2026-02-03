from app.models.collections import CANDIDATES_COLLECTION
from app.repositories.base import BaseRepository


class CandidateRepository(BaseRepository):
    collection_name = CANDIDATES_COLLECTION

    async def ensure_indexes(self) -> None:
        await self._collection.create_index([("request_id", 1)], name="idx_candidate_request")
        await self._collection.create_index([("developer_id", 1)], name="idx_candidate_developer")
        await self._collection.create_index(
            [("request_id", 1), ("developer_id", 1)],
            unique=True,
            name="uniq_candidate_request_developer",
        )
