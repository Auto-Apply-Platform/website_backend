from app.models.collections import REQUESTS_COLLECTION
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository):
    collection_name = REQUESTS_COLLECTION
