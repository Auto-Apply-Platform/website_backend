from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class MongoClient:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None

    def connect(self) -> AsyncIOMotorDatabase:
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongodb_uri)
        return self._client[settings.mongodb_db]

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


mongo_client = MongoClient()
