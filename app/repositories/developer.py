from app.models.collections import DEVELOPERS_COLLECTION
from app.repositories.base import BaseRepository


class DeveloperRepository(BaseRepository):
    collection_name = DEVELOPERS_COLLECTION

    async def list_distinct_values(self, field_name: str) -> list[str]:
        values = await self._collection.distinct(field_name)
        return [value for value in values if isinstance(value, str) and value.strip()]
