from app.models.collections import LOGS_COLLECTION
from app.repositories.base import BaseRepository


class LogRepository(BaseRepository):
    collection_name = LOGS_COLLECTION
