from app.models.collections import ROLES_COLLECTION
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository):
    collection_name = ROLES_COLLECTION

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("name", 1)],
            unique=True,
            name="uniq_role_name",
        )

    async def get_by_name(self, name: str) -> dict | None:
        return await self._collection.find_one({"name": name})

    async def list_roles(self) -> list[dict]:
        cursor = self._collection.find({}).sort("name", 1)
        return [doc async for doc in cursor]
