from app.models.collections import SOURCES_COLLECTION
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository):
    collection_name = SOURCES_COLLECTION
