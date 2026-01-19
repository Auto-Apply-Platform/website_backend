from app.models.collections import STAGES_COLLECTION
from app.repositories.base import BaseRepository


class StageRepository(BaseRepository):
    collection_name = STAGES_COLLECTION
