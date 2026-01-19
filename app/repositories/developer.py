from app.models.collections import DEVELOPERS_COLLECTION
from app.repositories.base import BaseRepository


class DeveloperRepository(BaseRepository):
    collection_name = DEVELOPERS_COLLECTION
